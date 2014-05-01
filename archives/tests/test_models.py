from __future__ import unicode_literals

from django.test import TestCase
from django.utils.text import slugify

from archives.models import Archive
from archives.policies import DefaultPolicy
from archives.transports import SshTransport, LocalTransport

from jenkins.tests.factories import BuildFactory, ArtifactFactory
from projects.tests.factories import DependencyFactory, ProjectFactory
from projects.models import ProjectDependency
from credentials.tests.factories import SshKeyPairFactory
from .factories import ArchiveFactory
from projects.helpers import build_project


class ArchiveTest(TestCase):
    def setUp(self):
        self.credentials = SshKeyPairFactory.create()

    def test_instantiation(self):
        """We can instantiate an Archive."""
        Archive.objects.create(
            name="My Test Archive",
            host="archive.example.com",
            policy="cdimage",
            transport="ssh",
            basedir="/var/tmp",
            username="testing",
            ssh_credentials=self.credentials)

    def test_get_transport(self):
        """
        Archive.get_transport should return the class to be used when moving
        files to an archive store.
        """
        archive = ArchiveFactory.create(transport="ssh")
        self.assertIsInstance(archive.get_transport(), SshTransport)

        archive.transport = "local"
        self.assertIsInstance(archive.get_transport(), LocalTransport)

    def test_get_policy(self):
        """
        Archive.get_policy should return the class to be used when deciding the
        names for files in the archive store.
        """
        archive = ArchiveFactory.create(policy="default")
        self.assertEqual(DefaultPolicy, archive.get_policy())

    def test_add_artifact(self):
        """
        An archive records the artifacts that get added.
        """
        artifact = ArtifactFactory.create()
        archive = ArchiveFactory.create()

        archive.add_artifact(artifact)
        self.assertEqual(1, archive.items.count())

    def test_add_artifact_repeatedly(self):
        """
        If we add the same artifact more than once, this shouldn't be an error,
        but no additional copies should be added.
        """
        artifact = ArtifactFactory.create()
        archive = ArchiveFactory.create()

        archive.add_artifact(artifact)
        archive.add_artifact(artifact)
        self.assertEqual(1, archive.items.count())

    def test_get_archived_artifact(self):
        """
        We can fetch the artifacts that get added.
        """
        artifact = ArtifactFactory.create(filename="artifact.gz")
        archive = ArchiveFactory.create()

        archive.add_artifact(artifact)
        archived = archive.get_archived_artifact(artifact)
        self.assertEqual(artifact, archived.artifact)
        self.assertEqual("artifact.gz", archived.archived_path)
        self.assertIsNone(archived.archived_at)

    def test_get_archived_artifact_artifact_not_in_archive(self):
        """
        If the specified artifact is not in the archive, we shold get None
        back.
        """
        artifact = ArtifactFactory.create()
        archive = ArchiveFactory.create()

        self.assertIsNone(archive.get_archived_artifact(artifact))

    def test_cdimage_archiver_policy(self):
        """
        If we use the cdimage policy, then the file path is quite different.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)

        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_key)

        artifact = ArtifactFactory.create(build=build, filename="testing.gz")
        archive = ArchiveFactory.create(policy="cdimage")

        archive.add_artifact(
            artifact, projectbuild=projectbuild)
        archived = archive.get_archived_artifact(artifact)
        self.assertEqual(artifact, archived.artifact)
        self.assertEqual(
            "%s/%s/testing.gz" % (
                slugify(project.name), projectbuild.build_id),
            archived.archived_path)
        self.assertIsNone(archived.archived_at)

    def test_archive_projectbuild(self):
        """
        The archiver can handle archiving an entire project build.
        """
        project = ProjectFactory.create()
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency1)
        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency2)

        projectbuild = build_project(project, queue_build=False)

        build1 = BuildFactory.create(
            job=dependency1.job, build_id=projectbuild.build_key)
        build2 = BuildFactory.create(
            job=dependency2.job, build_id=projectbuild.build_key)

        ArtifactFactory.create(build=build1, filename="artifact1.gz")
        ArtifactFactory.create(build=build2, filename="artifact2.gz")

        archive = ArchiveFactory.create()

        result = archive.archive_projectbuild(projectbuild)

        self.assertEqual(2, archive.items.count())
        self.assertEqual(2, len(result))

    def test_archive_projectbuild_with_prearchived_artifact(self):
        """
        If we archive a project build with several artifacts, it should return
        only the newly added artifacts.
        """
        project = ProjectFactory.create()
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency1)
        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency2)

        projectbuild = build_project(project, queue_build=False)

        build1 = BuildFactory.create(
            job=dependency1.job, build_id=projectbuild.build_key)
        build2 = BuildFactory.create(
            job=dependency2.job, build_id=projectbuild.build_key)

        ArtifactFactory.create(build=build1, filename="artifact1.gz")
        artifact = ArtifactFactory.create(
            build=build2, filename="artifact2.gz")
        archive = ArchiveFactory.create()

        archive.add_artifact(artifact, projectbuild=projectbuild)
        result = archive.archive_projectbuild(projectbuild)

        self.assertEqual(2, archive.items.count())
        self.assertEqual(1, len(result))
