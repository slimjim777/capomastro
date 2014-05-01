from django.db import models
from django.utils.encoding import python_2_unicode_compatible

from jenkins.models import Artifact

from credentials.models import SshKeyPair
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

    def __str__(self):
        return self.name

    def get_policy(self):
        """
        Returns a class to be used as the archive name generation policy for
        this archive or None.
        """
        return POLICIES.get(self.policy)

    def get_transport(self):
        """
        Returns a class to be used to archive files for this archive or None.
        """
        return TRANSPORTS.get(self.transport)(self)

    def add_artifact(self, artifact, **kwargs):
        """
        Add an Artifact for this project.
        """
        policy = self.get_policy()()
        if not self.items.filter(artifact=artifact).exists():
            item = self.items.create(
                artifact=artifact,
                archived_path=policy.get_path_for_artifact(artifact, **kwargs))
            return item

    def get_archived_artifact(self, artifact):
        """
        Get an artifact from the archive.
        """
        try:
            return self.items.get(artifact=artifact)
        except ArchiveArtifact.DoesNotExist:
            return

    def archive_projectbuild(self, projectbuild):
        """
        Convenience method for archiving projectbuilds.
        """
        items = []
        for artifact in projectbuild.get_current_artifacts():
            item = self.add_artifact(artifact, projectbuild=projectbuild)
            if item:
                items.append(item)
        return items



@python_2_unicode_compatible
class ArchiveArtifact(models.Model):

    archive = models.ForeignKey(Archive, related_name="items")
    artifact = models.ForeignKey(Artifact)
    archived_at = models.DateTimeField(blank=True, null=True)
    archived_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.archive.name
