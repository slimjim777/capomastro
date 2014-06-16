from __future__ import unicode_literals

import tempfile
import shutil
from io import StringIO
import os

from django.test import TestCase
import mock

from archives.models import ArchiveArtifact
from archives.transports import LocalTransport, SshTransport
from .factories import ArchiveFactory
from projects.tests.factories import (
    ProjectFactory, DependencyFactory, ProjectBuildFactory)
from projects.helpers import build_project
from projects.models import ProjectDependency, ProjectBuildDependency
from projects.tasks import process_build_dependencies
from jenkins.models import Artifact
from jenkins.tests.factories import ArtifactFactory, BuildFactory


class LocalTransportTest(TestCase):

    def setUp(self):
        self.basedir = tempfile.mkdtemp()
        self.archive = ArchiveFactory.create(
            transport="local", basedir=self.basedir)

    def tearDown(self):
        shutil.rmtree(self.basedir)

    def test_archive_file(self):
        """
        LocalTransport should copy the file from the supplied fileobj to a
        local path.
        """
        transport = LocalTransport(self.archive)
        fakefile = StringIO(u"This is the artifact")

        transport.archive_file(fakefile, "/temp/temp.gz")
        filename = os.path.join(self.basedir, "temp/temp.gz")
        self.assertEqual(file(filename).read(), "This is the artifact")

    def test_archive_from_url(self):
        """
        archive_from_url takes a valid URL and opens the file and then passes
        it to archive_file.
        """
        fakefile = StringIO(u"Entirely new artifact")

        mock_request = mock.Mock()
        with mock.patch("archives.transports.urllib2") as urllib2_mock:
            urllib2_mock.Request.return_value = mock_request
            transport = LocalTransport(self.archive)
            urllib2_mock.urlopen.return_value = fakefile
            transport.archive_url(
                "http://example.com/testing", "/temp/temp.gz",
                "username", "password")
        urllib2_mock.urlopen.assert_called_once_with(mock_request)
        urllib2_mock.Request.assert_called_once_with(
            "http://example.com/testing")
        mock_request.assert_has_calls(
            mock.call.add_header(
                "Authorization", "Basic dXNlcm5hbWU6cGFzc3dvcmQ="))
        filename = os.path.join(self.basedir, "temp/temp.gz")
        self.assertEqual(file(filename).read(), "Entirely new artifact")

    def test_start(self):
        """
        LocalTransport.start should ensure that the basedir exists.
        """
        dirname = os.path.join(self.basedir, "temp")
        self.archive.basedir = dirname
        transport = LocalTransport(self.archive)
        transport.start()

        self.assertTrue(os.path.exists(dirname))


class SshTransportTest(TestCase):

    def setUp(self):
        self.archive = ArchiveFactory.create(
            transport="ssh", basedir="/var/tmp")

    def test_get_ssh_clients(self):
        """
        _get_ssh_clients should return an SSHClient and SFTPClient configured
        to talk to the archive's credentials.
        """
        with mock.patch.object(
                self.archive.ssh_credentials, "get_pkey", return_value="KEY"):
            with mock.patch("archives.transports.SSHClient") as mock_client:
                mock_client.return_value.get_transport.return_value = "MockTransport"
                with mock.patch(
                        "archives.transports.SFTPClient") as mock_sftp:
                    with mock.patch(
                            "archives.transports.WarningPolicy") as mock_hostpolicy:
                        mock_hostpolicy.return_value = "MockWarningPolicy"
                        transport = SshTransport(self.archive)
                        transport._get_ssh_clients()

        mock_client.return_value.assert_has_calls([
            mock.call.set_missing_host_key_policy("MockWarningPolicy"),
            mock.call.connect(
                "archive.example.com", username="testing", pkey="KEY"),
            mock.call.get_transport()])
        mock_sftp.from_transport.assert_called_once_with("MockTransport")

    def test_archive_file(self):
        """
        archive_file should ensure that there's a directory relative to the
        base to hold the file, and then stream the file to the remote server.
        """
        mock_ssh = mock.Mock()
        mock_stdout = mock.Mock()
        mock_ssh.exec_command.return_value = None, mock_stdout, None
        mock_sftp = mock.Mock()
        fakefile = StringIO(u"This is the artifact")

        transport = SshTransport(self.archive)
        with mock.patch.object(
                transport, "_get_ssh_clients",
                return_value=(mock_ssh, mock_sftp)):
            transport.start()
            transport.archive_file(fakefile, "/temp/temp.gz")
        mock_ssh.exec_command.assert_called_once_with(
            "mkdir -p `dirname /var/tmp/temp/temp.gz`")

        mock_sftp.stream_file_to_remote.assert_called_once_with(
            fakefile, "/var/tmp/temp/temp.gz")

        mock_ssh.close.assert_called_once()

    def test_generate_checksums(self):
        """
        generate_checksums should send commands to the ssh client
        to generate an sha256sum for the passed in archived artifact.
        """
        # a project with a build and an archived artifact
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        projectdependency = ProjectDependency.objects.create(
            project=project, dependency=dependency)
        projectbuild = build_project(project, queue_build=False)
        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_key)
        projectbuild_dependency = ProjectBuildDependency.objects.create(
            build=build, projectbuild=projectbuild, dependency=dependency)
        artifact = ArtifactFactory.create(
            build=build, filename="artifact_filename")
        archived_artifact = ArchiveArtifact.objects.create(
            build=build, archive=self.archive, artifact=artifact,
            archived_path="/srv/builds/200101.01/artifact_filename",
            projectbuild_dependency=projectbuild_dependency)

        transport = SshTransport(self.archive)

        with mock.patch.object(transport, "_run_command") as mock_run:
            transport.generate_checksums(archived_artifact)

        mock_run.assert_called_once_with(
            "cd `dirname /srv/builds/200101.01/artifact_filename`; "
            "sha256sum artifact_filename >> SHA256SUMS")

