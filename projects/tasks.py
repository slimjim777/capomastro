from django.utils import timezone

from celery.utils.log import get_task_logger
from celery import shared_task

from archives.models import Archive
from projects.models import ProjectBuild

logger = get_task_logger(__name__)


def get_transport_for_projectbuild(projectbuild, archive):
    """
    Returns a transport for a projectbuild to be archived to a specific
    archive.
    """
    policy = archive.get_policy()(projectbuild)
    transport = archive.get_archiver()(policy, archive)
    return transport


@shared_task
def archive_projectbuild(projectbuild_pk, archive_pk):
    projectbuild = ProjectBuild.objects.get(pk=projectbuild_pk)
    archive = Archive.objects.get(pk=archive_pk)

    transport = get_transport_for_projectbuild(projectbuild, archive)

    transport.archive()
    projectbuild.archived = timezone.now()
    projectbuild.save()
