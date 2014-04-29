from __future__ import unicode_literals

from django.test import TestCase

from archives.policies import DefaultPolicy, CdimageArchivePolicy
from jenkins.tests.factories import BuildFactory, ArtifactFactory
from projects.tests.factories import DependencyFactory, ProjectFactory
from projects.models import ProjectDependency


class DefaultPolicyTest(TestCase):

    def test_get_path_for_artifact(self):
        """
        The default archive policy should return the path from the artifact
        url.
        """
        artifact = ArtifactFactory.create(filename="testing.img")
        policy = DefaultPolicy()
        self.assertEqual(
            "testing.img", policy.get_path_for_artifact(artifact))


class CdimageArchivePolicyTest(TestCase):

    def test_get_path_for_artifact(self):
        """
        The CdimageArchivePolicy should calculate a cdimage-like path using the
        project name and build id.
        url.
        """
        project = ProjectFactory.create(name="My Test Project")
        dependency = DependencyFactory.create()
        ProjectDependency.objects.create(
            project=project, dependency=dependency)

        from projects.helpers import build_project
        projectbuild = build_project(project, queue_build=False)

        build = BuildFactory.create(
            job=dependency.job, build_id=projectbuild.build_id)

        artifact = ArtifactFactory.create(
            filename="thing.txt", build=build)
        policy = CdimageArchivePolicy()
        self.assertEqual(
            "%s/%s/thing.txt" % ("my-test-project", build.build_id),
            policy.get_path_for_artifact(artifact, projectbuild=projectbuild))
