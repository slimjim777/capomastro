from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone
from django.dispatch import receiver

from projects.models import (
    Dependency, ProjectDependency, ProjectBuild, generate_projectbuild_id,
    ProjectBuildDependency, projectbuild_finished)
from .factories import (
    ProjectFactory, DependencyFactory, ProjectBuildFactory)
from jenkins.tests.factories import JobFactory, BuildFactory, ArtifactFactory


class DependencyTest(TestCase):

    def test_instantiation(self):
        """We can create Dependencies."""
        job = JobFactory.create()
        Dependency.objects.create(
            name="My Dependency", job=job)

    def test_get_current_build(self):
        """
        Dependency.get_current_build should return the most recent build that
        has completed and was SUCCESSful.
        """
        build1 = BuildFactory.create()
        build2 = BuildFactory.create(
            phase="FINISHED", status="SUCCESS", job=build1.job)
        dependency = DependencyFactory.create(job=build1.job)
        self.assertEqual(build2, dependency.get_current_build())

    def test_get_current_build_with_no_builds(self):
        """
        If there are no current builds for a given dependency, then we should
        get None.
        """
        dependency = DependencyFactory.create()
        self.assertEqual(None, dependency.get_current_build())

    def test_get_parameters(self):
        """
        Dependency.get_build_parameters should return a dictionary parsed from
        the parameters property.
        """
        dependency = DependencyFactory.create(
            parameters="THISVALUE=testing\nTHATVALUE=55")
        self.assertEqual(
            {"THISVALUE": "testing", "THATVALUE": "55"},
            dependency.get_build_parameters())

    def test_get_parameters_with_no_parameters(self):
        """
        Dependency.get_build_parameters should None if there are no build
        parameters.
        """
        dependency = DependencyFactory.create(parameters=None)
        self.assertIsNone(dependency.get_build_parameters())

    def test_is_dependency_building(self):
        """
        is_building should return True if we have an active build for
        this dependency in the works.
        """
        dependency = DependencyFactory.create()
        self.assertFalse(dependency.is_building)

        build = BuildFactory.create(job=dependency.job)
        self.assertTrue(dependency.is_building)


class ProjectDependencyTest(TestCase):

    def test_instantiation(self):
        """We can create ProjectDependency objects."""
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)
        self.assertEqual(
            set([dependency]), set(project.dependencies.all()))

    def test_auto_track_build(self):
        """
        If we create a new build for a dependency of a Project, and the
        ProjectDependency is set to auto_track then the current_build should be
        updated to reflect the new build.
        """
        build1 = BuildFactory.create()
        dependency = DependencyFactory.create(job=build1.job)

        project = ProjectFactory.create()
        project_dependency = ProjectDependency.objects.create(
            project=project, dependency=dependency)
        project_dependency.current_build = build1
        project_dependency.save()

        build2 = BuildFactory.create(job=build1.job)
        # Reload the project dependency
        project_dependency = ProjectDependency.objects.get(
            pk=project_dependency.pk)
        self.assertEqual(build2, project_dependency.current_build)

    def test_new_build_with_no_auto_track_build(self):
        """
        If we create a new build for a dependency of a Project, and the
        ProjectDependency is not set to auto_track then the current_build
        should not be updated.
        """
        build1 = BuildFactory.create()
        dependency = DependencyFactory.create(job=build1.job)

        project = ProjectFactory.create()
        project_dependency = ProjectDependency.objects.create(
            project=project, dependency=dependency, auto_track=False)
        project_dependency.current_build = build1
        project_dependency.save()

        BuildFactory.create(job=build1.job)
        # Reload the project dependency
        project_dependency = ProjectDependency.objects.get(
            pk=project_dependency.pk)
        self.assertEqual(build1, project_dependency.current_build)


class ProjectTest(TestCase):

    def test_get_current_artifacts(self):
        """
        Project.get_current_artifacts returns the current set of artifacts
        for this project.
        """
        project = ProjectFactory.create()
        job = JobFactory.create()
        dependency = DependencyFactory.create(job=job)
        ProjectDependency.objects.create(
            project=project, dependency=dependency)
        build1 = BuildFactory.create(job=job)
        build2 = BuildFactory.create(job=job)

        ArtifactFactory.create(build=build1)
        artifact2 = ArtifactFactory.create(build=build2)

        self.assertEqual([artifact2], list(project.get_current_artifacts()))


class ProjectBuildTest(TestCase):

    def setUp(self):
        self.project = ProjectFactory.create()
        self.user = User.objects.create_user("testing")

    def test_generate_projectbuild_id(self):
        """
        generate_projectbuild_id should generate an id using the date and the
        sequence of builds on that date.

        e.g. 20140312.1 is the first build on the 12th March 2014
        """
        build1 = ProjectBuildFactory.create()
        expected_build_id = timezone.now().strftime("%Y%m%d.1")
        self.assertEqual(expected_build_id, generate_projectbuild_id(build1))
        build2 = ProjectBuildFactory.create(project=build1.project)
        expected_build_id = timezone.now().strftime("%Y%m%d.2")
        self.assertEqual(expected_build_id, generate_projectbuild_id(build2))

    def test_build_key(self):
        """
        The build_key is a UUID for this project build.
        """
        build1 = ProjectBuildFactory.create()
        build2 = ProjectBuildFactory.create(project=build1.project)
        self.assertNotEqual(build1.build_key, build2.build_key)

    def test_instantiation(self):
        """
        We can create ProjectBuilds.
        """
        projectbuild = ProjectBuild.objects.create(
            project=self.project, requested_by=self.user)
        self.assertEqual(self.user, projectbuild.requested_by)
        self.assertIsNotNone(projectbuild.requested_at)
        self.assertIsNone(projectbuild.ended_at)
        self.assertEqual("UNKNOWN", projectbuild.status)
        self.assertEqual("UNKNOWN", projectbuild.phase)
        self.assertTrue(projectbuild.build_key)

    def test_build_id(self):
        """
        When we create a project build, we should create a unique id for the
        build.
        """
        projectbuild = ProjectBuildFactory.create()
        expected_build_id = timezone.now().strftime("%Y%m%d.0")
        self.assertEqual(expected_build_id, projectbuild.build_id)

    def test_projectbuild_updates_when_build_created(self):
        """
        If we have a ProjectBuild with a dependency, which is associated with a
        job, and we get a build from that job, then if the build_id is correct,
        we should associate the build dependency with that build.
        """
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency2)

        from projects.helpers import build_project
        projectbuild = build_project(self.project, queue_build=False)

        build1 = BuildFactory.create(
            job=dependency1.job, build_id=projectbuild.build_key)

        build_dependencies = ProjectBuildDependency.objects.filter(
            projectbuild=projectbuild)
        self.assertEqual(2, build_dependencies.count())
        dependency = build_dependencies.get(dependency=dependency1)
        self.assertEqual(build1, dependency.build)

        dependency = build_dependencies.get(dependency=dependency2)
        self.assertIsNone(dependency.build)

    def test_project_build_status_when_all_dependencies_have_builds(self):
        """
        When we have FINISHED builds for all the dependencies, the projectbuild
        state should be FINISHED.
        """
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency2)

        from projects.helpers import build_project
        projectbuild = build_project(self.project, queue_build=False)

        for job in [dependency1.job, dependency2.job]:
            BuildFactory.create(
                job=job, build_id=projectbuild.build_key, phase="FINISHED")

        projectbuild = ProjectBuild.objects.get(pk=projectbuild.pk)
        self.assertEqual("SUCCESS", projectbuild.status)
        self.assertEqual("FINISHED", projectbuild.phase)
        self.assertIsNotNone(projectbuild.ended_at)

    def test_project_build_sends_finished_signal(self):
        """
        When we set the projectbuild status to finished, we should signal this.
        """
        @receiver(projectbuild_finished, sender=ProjectBuild)
        def handle_signal(sender, projectbuild, **kwargs):
            self.projectbuild = projectbuild

        project = ProjectFactory.create()
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency2)

        from projects.helpers import build_project
        projectbuild = build_project(project, queue_build=False)

        for job in [dependency1.job, dependency2.job]:
            BuildFactory.create(
                job=job, build_id=projectbuild.build_key, phase="FINISHED")

        self.assertEqual(projectbuild, self.projectbuild)

    def test_can_be_archived(self):
        """
        A ProjectBuild knows whether or not it's ready to be archived.
        """
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency2)

        from projects.helpers import build_project
        projectbuild = build_project(self.project, queue_build=False)

        # Current status is STARTED so we can't archive this build.
        self.assertEqual("UNKNOWN", projectbuild.phase)
        self.assertFalse(projectbuild.can_be_archived)

        builds = []
        for job in [dependency1.job, dependency2.job]:
            builds.append(
                BuildFactory.create(
                    job=job, build_id=projectbuild.build_key,
                    phase="FINISHED"))
        projectbuild = ProjectBuild.objects.get(pk=projectbuild.pk)
        self.assertEqual("FINISHED", projectbuild.phase)

        self.assertFalse(
            projectbuild.can_be_archived,
            "Build with no artifacts can be archived")
        for build in builds:
            ArtifactFactory.create(build=build)
        self.assertTrue(
            projectbuild.can_be_archived,
            "Build with artifacts can't be archived")

        projectbuild.archived = timezone.now()
        self.assertFalse(projectbuild.can_be_archived)

    def test_can_be_archived_with_no_artifacts(self):
        """
        A projectbuild with no artifacts can't be archived.
        """
        dependency1 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency1)

        dependency2 = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency2)

        from projects.helpers import build_project
        projectbuild = build_project(self.project, queue_build=False)

        for job in [dependency1.job, dependency2.job]:
            BuildFactory.create(
                job=job, build_id=projectbuild.build_id, phase="FINISHED")
        projectbuild = ProjectBuild.objects.get(pk=projectbuild.pk)
        self.assertFalse(projectbuild.can_be_archived)
