from django.test import TestCase
from django.core.urlresolvers import reverse

from projects.helpers import build_project
from projects.templatetags.projects_tags import build_url
from projects.models import ProjectDependency
from projects.tests.factories import ProjectFactory, DependencyFactory
from jenkins.tests.factories import BuildFactory


class BuildUrlTest(TestCase):

    def test_build_url_with_projectbuild(self):
        """
        build_url should return the url for a project build if the build_id
        corresponds to a ProjectBuild.
        """
        project = ProjectFactory.create()
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        projectbuild = build_project(project, queue_build=False)
        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_key)

        expected_url = reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": project.pk, "build_pk": projectbuild.pk})
        self.assertEqual(expected_url, build_url(build.build_id))

    def test_build_url_with_non_projectbuild(self):
        """
        build_url should return an empty string for non-project builds.
        # TODO: This should link to a Build Detail page in the jenkins app.
        """
        build = BuildFactory.create()
        self.assertEqual("", build_url(build.build_id))
