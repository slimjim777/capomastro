from django.test import TestCase
from django.contrib.auth.models import User
import mock

from projects.models import (
    ProjectBuild, ProjectDependency, ProjectBuildDependency)
from projects.helpers import (
    build_project, build_dependency)
from .factories import ProjectFactory, DependencyFactory
from jenkins.tests.factories import BuildFactory


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
            [mock.call(dependency1.job.pk, build_id=new_build.build_key),
             mock.call(dependency2.job.pk, build_id=new_build.build_key)])

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
            dependency.job.pk, build_id=new_build.build_key,
            params={"THISVALUE": "mako"})

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

    def test_build_dependency_with_user(self):
        """
        build_dependency schedules the build of a dependency, and sets the
        requestor parameter if there's a request user.
        """
        dependency = DependencyFactory.create()
        user = User.objects.create_user("testing")

        with mock.patch("projects.helpers.build_job") as mock_build_job:
            build_dependency(dependency, build_id="201403.2", user=user)

        mock_build_job.delay.assert_called_once_with(
            dependency.job.pk, build_id="201403.2", user="testing")
