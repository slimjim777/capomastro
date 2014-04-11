from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from django_webtest import WebTest
import mock

from projects.models import (
    ProjectDependency, Project, Dependency, ProjectBuildDependency)
from projects.helpers import build_project
from jenkins.models import Job
from .factories import (
    ProjectFactory, DependencyFactory, ProjectBuildFactory)
from jenkins.tests.factories import (
    BuildFactory, JobFactory, JobTypeFactory, JenkinsServerFactory,
    ArtifactFactory)
from archives.tests.factories import ArchiveFactory


# TODO Introduce subclass of WebTest that allows easy assertions that a page
# requires various permissions...
# Possibly, through looking to see if Views are mixed in with the various
# Django-Braces mixins.


class ProjectDetailTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_project_detail(self):
        """
        The detail view should render the project.
        """
        project = ProjectFactory.create()
        # TODO: Work out how to configure DjangoFactory to setup m2m through
        dependency = ProjectDependency.objects.create(
            project=project, dependency=DependencyFactory.create())
        # TODO: It'd be nice if this was driven by ProjectBuildFactory.
        projectbuilds = [
            build_project(project, queue_build=False) for x in range(6)]

        project_url = reverse("project_detail", kwargs={"pk": project.pk})
        response = self.app.get(project_url, user="testing")
        self.assertEqual(200, response.status_code)
        self.assertEqual(project, response.context["project"])
        self.assertEqual([dependency], list(response.context["dependencies"]))
        self.assertEqual(
            projectbuilds[:5], list(response.context["projectbuilds"]))


class ProjectCreateTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "testing", "testing@example.com", "password")
        self.dependency1 = DependencyFactory.create()
        self.dependency2 = DependencyFactory.create()

    def test_page_requires_permission(self):
        """
        """
        # TODO: We should assert that requests without the
        # "projects.add_project" get redirected to login.

    def test_create_project_with_dependencies(self):
        """
        We can create projects with a set of dependencies.
        """
        project_url = reverse("project_create")
        response = self.app.get(project_url, user="testing")
        form = response.forms["project"]
        form["dependencies"].select_multiple(
            [self.dependency1.pk, self.dependency2.pk])
        form["name"].value = "My Project"

        response = form.submit()

        project = Project.objects.get(name="My Project")
        dependencies = ProjectDependency.objects.filter(project=project)

        self.assertEqual(
            [False, False],
            list(dependencies.values_list("auto_track", flat=True)))
        self.assertEqual(
            set([self.dependency1.name, self.dependency2.name]),
            set(dependencies.values_list("dependency__name", flat=True)))

    def test_create_project_with_auto_track(self):
        """
        We can set the auto_track on dependencies of the project.
        """
        project_url = reverse("project_create")
        response = self.app.get(project_url, user="testing")
        form = response.forms["project"]
        form["dependencies"].select_multiple(
            [self.dependency1.pk, self.dependency2.pk])
        form["name"].value = "My Project"
        form["auto_track"].value = True

        response = form.submit()

        project = Project.objects.get(name="My Project")
        dependencies = ProjectDependency.objects.filter(project=project)

        self.assertEqual(
            [True, True],
            list(dependencies.values_list("auto_track", flat=True)))

    def test_create_project_non_unique_name(self):
        """
        The project name should be unique.
        """
        ProjectFactory.create(name="My Project")

        project_url = reverse("project_create")
        response = self.app.get(project_url, user="testing")
        form = response.forms["project"]
        form["dependencies"].select_multiple(
            [self.dependency1.pk])
        form["name"].value = "My Project"

        response = form.submit()
        self.assertContains(response, "Project with this Name already exists.")


class ProjectBuildListTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_projectbuild_list_view(self):
        """
        The list view should provide a list of projects.
        """
        job = JobFactory.create()
        BuildFactory.create_batch(5, job=job)

        project = ProjectFactory.create()

        ProjectDependency.objects.create(
            project=project, dependency=DependencyFactory.create(job=job))
        projectbuild = ProjectBuildFactory.create(project=project)
        BuildFactory.create(job=job, build_id=projectbuild.build_id)

        url = reverse("project_projectbuild_list", kwargs={"pk": project.pk})
        response = self.app.get(url, user="testing")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            set([projectbuild]), set(response.context["projectbuilds"]))
        self.assertEqual(project, response.context["project"])


class ProjectBuildDetailTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_user("testing")
        self.project = ProjectFactory.create()

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_project_build_detail_view(self):
        """
        Project build detail should show the build.
        """
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency)

        projectbuild = build_project(self.project, queue_build=False)
        BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_id)

        url = reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": self.project.pk,
                    "build_pk": projectbuild.pk})
        response = self.app.get(url, user="testing")

        dependencies = ProjectBuildDependency.objects.filter(
            projectbuild=projectbuild)

        self.assertEqual(projectbuild, response.context["projectbuild"])
        self.assertEqual(
            list(dependencies), list(response.context["dependencies"]))
        self.assertFalse(
            response.context["can_be_archived"],
            "Build with no artifacts can be archived")
        self.assertIsNone(response.forms.get("archivebuild-form"))
        self.assertContains(response, "Build cannot currently be archived.")

    def test_project_build_detail_view_already_archived(self):
        """
        If a projectbuild has the archived date set, then it has already been
        archived.
        """
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency)

        projectbuild = build_project(self.project, queue_build=False)
        projectbuild.archived = timezone.now()
        projectbuild.save()
        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_id)
        ArtifactFactory.create(build=build)

        url = reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": self.project.pk,
                    "build_pk": projectbuild.pk})
        response = self.app.get(url, user="testing")
        self.assertFalse(
            response.context["can_be_archived"], "Build can be archived")

    def test_project_build_can_be_archived(self):
        """
        If a projectbuild has the archived date set, then it has already been
        archived.
        """
        archive = ArchiveFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=self.project, dependency=dependency)

        projectbuild = build_project(self.project, queue_build=False)
        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_id,
            phase="FINISHED")
        ArtifactFactory.create(build=build)

        url = reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": self.project.pk,
                    "build_pk": projectbuild.pk})

        response = self.app.get(url, user="testing")
        self.assertTrue(
            response.context["can_be_archived"], "Build cannot be archived")

        form = response.forms["archivebuild-form"]
        form["archive"].select(archive.pk)

        with mock.patch(
                "projects.views.archive_projectbuild") as archive_build_mock:
            response = form.submit().follow()

        archive_build_mock.delay.assert_called_once_with(
            projectbuild.pk, archive.pk)
        self.assertContains(
            response,
            "Archiving for '%s' queued." % projectbuild.build_id)


class DependencyListTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_dependency_list_view(self):
        """
        The Dependency List should render a list of dependencies with links to
        their type detail views.
        """
        dependencies = DependencyFactory.create_batch(5)
        url = reverse("dependency_list")
        response = self.app.get(url, user="testing")

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            set(dependencies), set(response.context["dependencies"]))

        response = response.click(dependencies[0].job.jobtype.name)
        self.assertEqual(
            dependencies[0].job.jobtype.name, response.html.title.text)


class DependencyCreateTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "testing", "testing@example.com", "password")
        self.jobtype = JobTypeFactory.create(
            config_xml="this is the job xml")
        self.server = JenkinsServerFactory.create()

    def test_page_requires_permission(self):
        """
        """
        # TODO: We should assert that requests without the
        # "projects.add_dependency" get redirected to login.

    def test_create_dependency(self):
        """
        We can create dependencies with jobs in servers.
        """
        project_url = reverse("dependency_create")
        response = self.app.get(project_url, user="testing")

        form = response.forms["dependency-form"]
        form["jobtype"].select(self.jobtype.pk)
        form["server"].select(self.server.pk)
        form["name"].value = "My Dependency"
        form["parameters"].value = "MYVALUE=this is a test\nNEWVALUE=testing"

        with mock.patch("projects.forms.push_job_to_jenkins") as job_mock:
            response = form.submit().follow()

        new_dependency = Dependency.objects.get(name="My Dependency")
        job = Job.objects.get(jobtype=self.jobtype, server=self.server)
        job_mock.delay.assert_called_once_with(job.pk)
        self.assertEqual(new_dependency.job, job)
        self.assertEqual(
            "MYVALUE=this is a test\nNEWVALUE=testing",
            new_dependency.parameters)


class DependencyDetailTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "testing", "testing@example.com", "password")

    def test_dependency_detail(self):
        """
        The dependency detail page should show recent builds, and associated
        projects.
        """
        dependency = DependencyFactory.create()
        project = ProjectFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)
        url = reverse("dependency_detail", kwargs={"pk": dependency.pk})
        response = self.app.get(url, user="testing")

        self.assertEqual(dependency, response.context["dependency"])
        self.assertEqual([project], list(response.context["projects"]))

    def test_dependency_build(self):
        """
        It's possible to request a build of a dependency from the dependendency
        detail page.
        """
        dependency = DependencyFactory.create()
        project = ProjectFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)
        url = reverse("dependency_detail", kwargs={"pk": dependency.pk})
        response = self.app.get(url, user="testing")

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = response.forms["build-dependency"].submit().follow()

        self.assertEqual(dependency, response.context["dependency"])
        self.assertEqual([project], list(response.context["projects"]))
        self.assertContains(
            response, "Build for '%s' queued." % dependency.name)
        build_job_mock.delay.assert_called_once_with(
            dependency.job.pk)

    def test_dependency_build_with_parameters(self):
        """
        If the dependency we're building has parameters, these should be passed
        with the job queue.
        """
        dependency = DependencyFactory.create(parameters="TESTPARAMETER=500")
        project = ProjectFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)
        url = reverse("dependency_detail", kwargs={"pk": dependency.pk})
        response = self.app.get(url, user="testing")

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = response.forms["build-dependency"].submit().follow()

        self.assertEqual(dependency, response.context["dependency"])
        self.assertEqual([project], list(response.context["projects"]))
        self.assertContains(
            response, "Build for '%s' queued." % dependency.name)
        build_job_mock.delay.assert_called_once_with(
            dependency.job.pk, params={"TESTPARAMETER": "500"})


class InitiateProjectBuildTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "testing", "testing@example.com", "password")

    def test_page_requires_permission(self):
        """
        """
        # TODO: We should assert that requests without the
        # "projects.add_projectbuild" get redirected to login.

    def test_project_build_form_selected_dependencies(self):
        """
        We expect all dependencies to be selected by default.
        """
        [dep1, dep2, dep3] = DependencyFactory.create_batch(3)
        project = ProjectFactory.create()
        for dep in [dep1, dep2, dep3]:
            ProjectDependency.objects.create(
                project=project, dependency=dep)
        url = reverse(
            "project_initiate_projectbuild", kwargs={"pk": project.pk})
        response = self.app.get(url, user="testing")
        form = response.forms["buildproject-form"]
        # We expect all dependencies to be selected by default
        self.assertEqual(
            [str(x.pk) for x in [dep1, dep2, dep3]],
            [x.value for x in form.fields["dependencies"]])

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = form.submit().follow()

        projectbuild = response.context["projectbuild"]

        build_job_mock.delay.assert_has_calls([
            mock.call(dep1.job.pk, build_id=projectbuild.build_id),
            mock.call(dep2.job.pk, build_id=projectbuild.build_id),
            mock.call(dep3.job.pk, build_id=projectbuild.build_id)])
        self.assertContains(
            response, "Build '%s' queued." % projectbuild.build_id)

    def test_project_build_form_builds_only_selected(self):
        """
        We expect all dependencies to be selected by default.
        """
        [dep1, dep2, dep3] = DependencyFactory.create_batch(3)
        project = ProjectFactory.create()
        for dep in [dep1, dep2, dep3]:
            ProjectDependency.objects.create(
                project=project, dependency=dep)
        url = reverse(
            "project_initiate_projectbuild", kwargs={"pk": project.pk})
        response = self.app.get(url, user="testing")
        form = response.forms["buildproject-form"]

        form["dependencies"] = [str(dep1.pk), str(dep3.pk)]

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = form.submit().follow()

        projectbuild = response.context["projectbuild"]

        build_job_mock.delay.assert_has_calls([
            mock.call(dep1.job.pk, build_id=projectbuild.build_id),
            mock.call(dep3.job.pk, build_id=projectbuild.build_id)])

    def test_project_build_form_requires_selection(self):
        """
        If no dependencies are selected, then we should get an appropriate
        error.
        """
        [dep1, dep2, dep3] = DependencyFactory.create_batch(3)
        project = ProjectFactory.create()
        for dep in [dep1, dep2, dep3]:
            ProjectDependency.objects.create(
                project=project, dependency=dep)
        url = reverse(
            "project_initiate_projectbuild", kwargs={"pk": project.pk})
        response = self.app.get(url, user="testing")
        form = response.forms["buildproject-form"]

        form["dependencies"] = []

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = form.submit()

        self.assertContains(response, "Must select at least one dependency.")
        self.assertEqual([], build_job_mock.delay.mock_calls)


class ProjectUpdateTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_superuser(
            "testing", "testing@example.com", "password")

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_project_update(self):
        """
        The update view should allow us to change the auto track status of the
        dependencies and add additional dependencies.
        """
        project = ProjectFactory.create()
        # TODO: Work out how to configure DjangoFactory to setup m2m through
        projectdependency1 = ProjectDependency.objects.create(
            project=project, dependency=DependencyFactory.create())

        projectdependency2 = ProjectDependency.objects.create(
            project=project, dependency=DependencyFactory.create())

        project_url = reverse("project_update", kwargs={"pk": project.pk})
        response = self.app.get(project_url, user="testing")
        self.assertEqual(200, response.status_code)

        form = response.forms["project"]
        self.assertEqual(
            [str(projectdependency1.dependency.pk),
             str(projectdependency2.dependency.pk)],
            form["dependencies"].value)
        self.assertEqual(project.name, form["name"].value)

        form["dependencies"].select_multiple(
            [projectdependency2.dependency.pk])
        form.submit().follow()

        self.assertEqual(1, len(project.dependencies.all()))


class ProjectDependenciesTest(WebTest):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_page_requires_authenticated_user(self):
        """
        """
        # TODO: We should assert that requests without a logged in user
        # get redirected to login.

    def test_project_dependencies(self):
        """
        Project Dependencies view should show all dependencies and the status
        of their build.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        builds = BuildFactory.create_batch(5, job=dependency.job)
        ProjectDependency.objects.create(
            project=project, dependency=dependency, auto_track=False,
            current_build=builds[-1])

        project_url = reverse(
            "project_dependencies", kwargs={"pk": project.pk})
        response = self.app.get(project_url, user="testing")
        self.assertEqual(200, response.status_code)
        self.assertEqual(project, response.context["project"])

        self.assertEqual(
            [dependency],
            list(response.context["builds_header"]))
