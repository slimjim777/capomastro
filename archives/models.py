import logging
import urlparse

from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from jenkins.models import Artifact, Build
from credentials.models import SshKeyPair
from projects.models import ProjectBuildDependency, Dependency
from archives.policies import CdimageArchivePolicy, DefaultPolicy
from archives.transports import SshTransport, LocalTransport


POLICIES = {"cdimage": CdimageArchivePolicy,
            "default": DefaultPolicy}
TRANSPORTS = {"ssh": SshTransport, "local": LocalTransport}


@python_2_unicode_compatible
class Archive(models.Model):

    name = models.CharField(max_length=64)
    host = models.CharField(max_length=64, blank=True, null=True)
    policy = models.CharField(
        max_length=64, choices=[(p, p) for p in POLICIES.keys()],
        default="default")
    basedir = models.CharField(max_length=128)
    username = models.CharField(max_length=64, blank=True, null=True)
    ssh_credentials = models.ForeignKey(SshKeyPair, blank=True, null=True)
    transport = models.CharField(
        max_length=64, choices=[(p, p) for p in TRANSPORTS.keys()])
    default = models.BooleanField(default=False)
    base_url = models.CharField(max_length=200, blank=True, default="")

    def __str__(self):
        return self.name

    def get_policy(self):
        """
        Returns a class to be used as the archive name generation policy for
        this archive or None.
        """
        return POLICIES.get(self.policy)()

    def get_transport(self):
        """
        Returns a class to be used to archive files for this archive or None.
        """
        return TRANSPORTS.get(self.transport)(self)

    def add_build(self, build):
        """
        Adds a build, with all artifacts to the archive.

        If this is a dependency build with no project dependencies, then we can
        simply archive that item.

        Otherwise we archive the item, and add each of the projectbuild
        dependencies too.
        """
        logging.info("Adding build %s", build)
        # Is this a project build dependency, or just a dependency build?
        if not build.projectbuild_dependencies.exists():
            items = self.add_dependency_build(build)
        else:
            items = self.add_dependency_build(build)
            for artifact, files in self.add_projectbuild(build).items():
                items.setdefault(artifact, []).extend(files)
        return items

    def add_dependency_build(self, build):
        """
        This adds dependency-only builds to the archive.
        """
        logging.info("    processing dependency builds")
        items = {}
        for artifact in build.artifact_set.all():
            logging.info("Adding artifact %s", artifact)
            for dependency in build.job.dependency_set.all():
                items.setdefault(artifact, []).append(self.add_artifact(
                    artifact, build, dependency=dependency))
        return items

    def add_projectbuild(self, build):
        """
        This adds projectbuild builds to the archive.
        """
        logging.info("    processing projectbuilds")
        items = {}
        for artifact in build.artifact_set.all():
            for dependency in build.projectbuild_dependencies.all():
                logging.info("Adding artifact %s", artifact)
                items.setdefault(artifact, []).append(self.add_artifact(
                    artifact, build, dependency=dependency.dependency,
                    projectbuild_dependency=dependency))
        return items

    def add_artifact(
            self, artifact, build, dependency=None,
            projectbuild_dependency=None):
        """
        Add an Artifact for this project.
        """
        policy = self.get_policy()
        projectbuild = (
            projectbuild_dependency and projectbuild_dependency.projectbuild)
        archived_path = policy.get_path_for_artifact(
            artifact, build=build, dependency=dependency,
            projectbuild=projectbuild)
        return self.items.create(
            artifact=artifact,
            dependency=dependency,
            build=build,
            projectbuild_dependency=projectbuild_dependency,
            archived_path=archived_path)

    def get_archived_artifacts_for_build(self, build):
        """
        Returns all artifacts for a specific build.
        """
        return self.items.filter(build=build)


@python_2_unicode_compatible
class ArchiveArtifact(models.Model):

    archive = models.ForeignKey(Archive, related_name="items")
    artifact = models.ForeignKey(Artifact)
    archived_at = models.DateTimeField(blank=True, null=True)
    archived_path = models.CharField(max_length=255, blank=True, null=True)
    archived_size = models.IntegerField(default=0)

    build = models.ForeignKey(Build, blank=True, null=True)
    projectbuild_dependency = models.ForeignKey(
        ProjectBuildDependency, blank=True, null=True)
    dependency = models.ForeignKey(
        Dependency, blank=True, null=True)

    class Meta:
        ordering = ["archived_path"]

    def __str__(self):
        return "%s %s" % (self.archived_path, self.archive)

    def get_url(self):
        """
        Return a combination of the base_url and archived_path for a given
        artifact combination.
        """
        return urlparse.urljoin(
            self.archive.base_url, self.archived_path.lstrip("/"))
