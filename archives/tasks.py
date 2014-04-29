import logging
import urlparse

from django.utils import timezone

from celery.utils.log import get_task_logger
from celery import shared_task

from archives.helpers import get_default_archive
from archives.models import Archive
from projects.models import ProjectBuildDependency
from jenkins.models import Build

logger = get_task_logger(__name__)


@shared_task
def archive_artifact_from_jenkins(artifact_pk, archive_pk):
    """
    Schedule the transfer of the file in the artifact to the specified archive.
    """
    archive = Archive.objects.get(pk=archive_pk)
    item = archive.items.get(artifact__pk=artifact_pk)

    transport = archive.get_transport()
    artifact = item.artifact
    server = artifact.build.job.server
    transport.start()
    transport.archive_url(
        artifact.url, item.archived_path,
        username=server.username, password=server.password)
    transport.end()
    item.archived_at = timezone.now()
    item.save()


# TODO Workout some sort of decorator so these functions don't have to return
# build_pk in the chain
@shared_task
def process_build_artifacts(build_pk):
    """
    This task should be triggered after we've imported the artifacts from
    Jenkins for a build.
    """
    build = Build.objects.get(pk=build_pk)
    logger.info("Processing build artifacts from build %s" % build)
    if build.build_id:
        dependency = ProjectBuildDependency.objects.filter(
            dependency__job=build.job,
            projectbuild__build_key=build.build_id).first()
        # TODO: Handle generic dependency builds.
        if dependency:
            projectbuild = dependency.projectbuild
            archive = get_default_archive()
            if archive:
                items = archive.archive_projectbuild(projectbuild)
                for item in items:
                    archive_artifact_from_jenkins.delay(item.artifact.pk, archive.pk)
            else:
                logger.info("No default archiver - projectbuild not automatically archived.")
    return build_pk
