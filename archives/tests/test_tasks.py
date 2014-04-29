from __future__ import unicode_literals

from io import StringIO
import os
import shutil
import tempfile

from django.test import TestCase
from django.test.utils import override_settings

import mock

from archives.tasks import (
    archive_artifact_from_jenkins, process_build_artifacts)
from archives.models import Archive
from archives.transports import Transport
from jenkins.tests.factories import ArtifactFactory, BuildFactory
from projects.helpers import build_project
from projects.models import ProjectDependency
from projects.tests.factories import DependencyFactory, ProjectFactory
from .factories import ArchiveFactory


class LoggingTransport(Transport):
    """
    Test archiver that just logs the calls the Archiver
    code makes.
    """
    log = []

    def start(self):
        self.log.append("START")

    def end(self):
        self.log.append("END")

    def archive_url(self, url, path, username, password):
        self.log.append("%s -> %s %s:%s" % (url, path, username, password))


class TransferFileToArchiveTaskTest(TestCase):

    def setUp(self):
        self.basedir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.basedir)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_archive_artifact_from_jenkins(self):
        """
        archive_artifact_from_jenkins should get a transport, and then call
        start, end and archive_artifact on the transport.
        the correct storage.
        """
        archive = ArchiveFactory.create(
            transport="local", basedir=self.basedir)

        artifact = ArtifactFactory.create(filename="testing/testing.txt")
        archive.add_artifact(artifact)

        fakefile = StringIO(u"Artifact from Jenkins")
        with mock.patch("archives.transports.urllib2") as urllib2_mock:
            urllib2_mock.urlopen.return_value = fakefile
            archive_artifact_from_jenkins.delay(artifact.pk, archive.pk)

        item = archive.get_archived_artifact(artifact)
        filename = os.path.join(self.basedir, item.archived_path)
        self.assertEqual(file(filename).read(), "Artifact from Jenkins")

    def test_archive_artifact_from_jenkins_transport_lifecycle(self):
        """
        archive_artifact_from_jenkins should get a transport, and copy the file to
        the correct storage.
        """
        archive = ArchiveFactory.create(
            transport="local", basedir=self.basedir)

        artifact = ArtifactFactory.create(filename="testing/testing.txt")
        item = archive.add_artifact(artifact)
        self.assertIsNone(item.archived_at)

        transport = LoggingTransport(archive)
        with mock.patch.object(Archive, "get_transport", return_value=transport) as archive_mock:
            archive_artifact_from_jenkins(artifact.pk, archive.pk)

        self.assertEqual(
            ["START",
             "%s -> testing/testing.txt root:testing" % artifact.url,
             "END"],
            transport.log)

        item = archive.get_archived_artifact(artifact)
        self.assertIsNotNone(item.archived_at)


class ProcessBuildArtifactsTaskTest(TestCase):

    def setUp(self):
        self.basedir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.basedir)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_process_build_artifacts(self):
        """
        process_build_artifacts is chained from the Jenkins postbuild
        processing, it should arrange for the artifacts for the provided build
        to be archived in the default archive.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)

        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_key)
        artifact = ArtifactFactory.create(
            build=build, filename="testing/testing.txt")
        archive = ArchiveFactory.create(
            transport="local", basedir=self.basedir, default=True)

        fakefile = StringIO(u"Artifact from Jenkins")
        with mock.patch("archives.transports.urllib2") as urllib2_mock:
            urllib2_mock.urlopen.return_value = fakefile
            process_build_artifacts.delay(build.pk)

        item = archive.get_archived_artifact(artifact)
        filename = os.path.join(self.basedir, item.archived_path)
        self.assertEqual(file(filename).read(), "Artifact from Jenkins")

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_process_build_artifacts_with_no_default_archive(self):
        """
        If we have no default archive, we should log the fact that we can't
        automatically archive artifacts.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)

        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_key)
        artifact = ArtifactFactory.create(
            build=build, filename="testing/testing.txt")
        archive = ArchiveFactory.create(
            transport="local", basedir=self.basedir, default=False)


        with mock.patch("archives.tasks.logger") as mock_logging:
            result = process_build_artifacts.delay(build.pk)

        # We must return the build.pk for further chained calls to work.
        self.assertEqual(build.pk, result.get())

        mock_logging.assert_has_calls([
            mock.call.info("Processing build artifacts from build %s" % build),
            mock.call.info(
              "No default archiver - projectbuild not automatically archived.")
        ])

        self.assertIsNone(archive.get_archived_artifact(artifact))
