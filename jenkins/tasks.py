from celery.utils.log import get_task_logger
from celery import shared_task

from jenkins.helpers import import_build_for_job
from jenkins.models import Job
from jenkins.utils import get_job_xml_for_upload

logger = get_task_logger(__name__)


@shared_task
def import_build(job_id, build_number):
    import_build_for_job(job_id, build_number)


@shared_task
def build_job(job_pk, build_id=None, params=None):
    """
    Request building Job.
    """
    # TODO: If a job is already queued, then this can throw
    # WillNotBuild: <jenkinsapi.job.Job job> is already queued
    job = Job.objects.get(pk=job_pk)
    client = job.server.get_client()
    if params is None:
        params = {}
    if build_id is not None:
        params["BUILD_ID"] = build_id
    client.build_job(job.name, params=params)


@shared_task
def push_job_to_jenkins(job_pk):
    """
    Create or update a job in the server with the config.
    """
    job = Job.objects.get(pk=job_pk)
    xml = get_job_xml_for_upload(job, job.server)
    client = job.server.get_client()

    if client.has_job(job.name):
        job = client.get_job(job.name)
        job.update_config(xml)
    else:
        client.create_job(job.name, xml)
