from django.test import TestCase

import mock

from projects.models import ProjectDependency, ProjectBuild
from projects.helpers import build_project
from projects.tasks import (
    archive_projectbuild, get_transport_for_projectbuild)
from .factories import ProjectFactory, DependencyFactory
from jenkins.tests.factories import BuildFactory, ArtifactFactory
from archives.tests.factories import ArchiveFactory


class ArchiveProjectBuildTaskTest(TestCase):

    def test_get_transport_for_projectbuild(self):
        """
        get_transport_for_projectbuild returns an Archiver ready to archive a
        project build.
        """
        archive = ArchiveFactory.create()
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)
        mock_policy = mock.Mock()

        with mock.patch.multiple(
                archive, get_archiver=mock.DEFAULT,
                get_policy=mock.DEFAULT) as mock_archive:
            mock_archive["get_policy"].return_value = mock_policy
            get_transport_for_projectbuild(projectbuild, archive)

        mock_policy.assert_called_once_with(projectbuild)
        mock_archive["get_archiver"].return_value.assert_called_once_with(
            mock_policy.return_value, archive)

    def test_archive_projectbuild(self):
        """
        Archive project build should create an archiver and archive it.
        """
        archive = ArchiveFactory.create()
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)
        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_id)
        ArtifactFactory.create_batch(3, build=build)

        with mock.patch(
                "projects.tasks.get_transport_for_projectbuild") as mock_archive:
            archive_projectbuild(projectbuild.pk, archive.pk)

        mock_archive.return_value.assert_has_calls(
            [mock.call.archive()])
        projectbuild = ProjectBuild.objects.get(pk=projectbuild.pk)
        self.assertTrue(projectbuild.archived)
