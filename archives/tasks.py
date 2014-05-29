import logging

from django.utils import timezone

from celery import shared_task

from archives.helpers import get_default_archive
from archives.models import ArchiveArtifact
from jenkins.models import Build


@shared_task
def archive_artifact_from_jenkins(archiveartifact_pk):
    """
    Schedule the transfer of the file in the artifact to the specified archive.
    """
    item = ArchiveArtifact.objects.get(pk=archiveartifact_pk)
    logging.info("Archiving %s in archive %s", item, item.archive)

    transport = item.archive.get_transport()
    artifact = item.artifact
    server = artifact.build.job.server
    transport.start()
    logging.info("  %s -> %s", artifact.url, item.archived_path)
    transport.archive_url(
        item.artifact.url, item.archived_path,
        username=server.username, password=server.password)
    transport.end()
    item.archived_at = timezone.now()
    logging.info("  archived at %s", item.archived_at)
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
    logging.info("Processing build artifacts from build %s %d", build, build_pk)
    archive = get_default_archive()
    if archive:
       items = archive.add_build(build)
       logging.info("Archiving %s", items)
       for item in items:
           archive_artifact_from_jenkins.delay(item.pk)
    else:
        logging.info("No default archiver - build not automatically archived.")
    return build_pk
