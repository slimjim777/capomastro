from celery.utils.log import get_task_logger
from celery import shared_task

from projects.helpers import archive_projectbuild as archive_build
from archives.models import Archive
from projects.models import ProjectBuild

logger = get_task_logger(__name__)


@shared_task
def archive_projectbuild(projectbuild_pk, archive_pk):
    projectbuild = ProjectBuild.objects.get(pk=projectbuild_pk)
    archive = Archive.objects.get(pk=archive_pk)
    archive_build(projectbuild, archive)
