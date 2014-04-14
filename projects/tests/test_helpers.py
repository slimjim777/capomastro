from django.test import TestCase
from django.contrib.auth.models import User
import mock

from projects.models import (
    ProjectBuild, ProjectDependency, ProjectBuildDependency)
from projects.helpers import (
    build_project, build_dependency, archive_projectbuild)
from .factories import ProjectFactory, DependencyFactory
from jenkins.tests.factories import BuildFactory, ArtifactFactory
from archives.tests.factories import ArchiveFactory


class BuildProjectTest(TestCase):

    def test_build_project(self):
        """
        build_project should create build dependencies for each of the project
        dependencies and schedule builds of each.
        """
        project = ProjectFactory.create()
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency2)

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            new_build = build_project(project)
            self.assertIsInstance(new_build, ProjectBuild)

        build_dependencies = ProjectBuildDependency.objects.filter(
            projectbuild=new_build)
        self.assertEqual(2, build_dependencies.count())
        self.assertEqual(
            [dependency1.pk, dependency2.pk],
            list(build_dependencies.values_list("dependency", flat=True)))
        mock_build_job.delay.assert_has_calls(
            [mock.call(dependency1.job.pk, build_id=new_build.build_id),
             mock.call(dependency2.job.pk, build_id=new_build.build_id)])

    def test_build_project_with_no_queue_build(self):
        """
        If we pass queue_build = False to build_project, then no builds should
        happen.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            build_project(project)

        self.assertItemsEqual([], mock_build_job.call_args_list)

    def test_build_project_with_dependency_with_parameters(self):
        """
        build_project should create pass the parameters for a dependency to the
        build_job request.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create(parameters="THISVALUE=mako")
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            new_build = build_project(project)
            self.assertIsInstance(new_build, ProjectBuild)

        mock_build_job.delay.assert_called_once_with(
            dependency.job.pk, build_id=new_build.build_id,
            params={"THISVALUE": "mako"})

    def test_build_project_with_specified_dependencies(self):
        """
        If a list of dependencies is provided, then we should only build those
        dependencies.
        """
        [dep1, dep2, dep3] = DependencyFactory.create_batch(3)
        project = ProjectFactory.create()
        for dep in [dep1, dep2, dep3]:
            ProjectDependency.objects.create(
                project=project, dependency=dep, auto_track=True)

        build = BuildFactory.create(job=dep1.job)
        # Reload object from database.
        project_dep1 = ProjectDependency.objects.get(
            project=project, dependency=dep1)
        self.assertEqual(build, project_dep1.current_build)

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            new_build = build_project(project, dependencies=[dep1, dep2])

        projectbuild_dependencies = ProjectBuildDependency.objects.filter(
            projectbuild=new_build)
        self.assertEqual(3, projectbuild_dependencies.all().count())
        self.assertEqual(
            set([dep1, dep2, dep3]),
            set([x.dependency for x in projectbuild_dependencies.all()]))

        mock_build_job.delay.assert_has_calls(
            [mock.call(dep1.job.pk, build_id=new_build.build_id),
             mock.call(dep2.job.pk, build_id=new_build.build_id)])

    def test_build_project_assigns_user_correctly(self):
        """
        If we pass a user to build_project, the user is assigned as the user
        for the projectbuild.
        """
        user = User.objects.create_user("testing")
        project = ProjectFactory.create()
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency1)

        new_build = build_project(project, user=user, queue_build=False)
        self.assertEqual(user, new_build.requested_by)


class BuildDependencyTest(TestCase):

    def test_build_dependency(self):
        """
        build_dependency schedules the build of a dependency.
        """
        dependency = DependencyFactory.create()

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            build_dependency(dependency)

        mock_build_job.delay.assert_called_once_with(dependency.job.pk)

    def test_build_dependency_with_parameters(self):
        """
        build_dependency schedules the build of a dependency along with any
        parameters.
        """
        dependency = DependencyFactory.create(
            parameters="THISVAL=500\nTHATVAL=testing")

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            build_dependency(dependency)

        mock_build_job.delay.assert_called_once_with(
            dependency.job.pk, params={"THISVAL": "500", "THATVAL": "testing"})

    def test_build_dependency_with_build_id(self):
        """
        build_dependency schedules the build of a dependency along with the
        build_id.
        """
        dependency = DependencyFactory.create()

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            build_dependency(dependency, build_id="201403.2")

        mock_build_job.delay.assert_called_once_with(
            dependency.job.pk, build_id="201403.2")


class ArchiveProjectBuildTest(TestCase):

    def test_archive_projectbuild(self):
        """
        The archive_projectbuild helper should kick off the task to archive the
        project.
        """
        archive = ArchiveFactory.create()
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)
        with mock.patch("projects.helpers.archive_projectbuild_task") as mock_task:
            archive_projectbuild(projectbuild, archive)
        mock_task.delay.assert_called_once_with(projectbuild.pk, archive.pk)
