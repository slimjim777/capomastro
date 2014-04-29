from django.test import TestCase
from django.test.utils import override_settings

from celery import shared_task
import mock

from jenkins.helpers import postprocess_build, create_job
from jenkins.models import Job
from jenkins.tasks import import_build_for_job
from .factories import (
    JobFactory, BuildFactory, JobTypeFactory, JenkinsServerFactory)


class CreateJobTest(TestCase):

    def test_create_job(self):
        """
        Create job should instantiate a job associated with a server and
        generate a name for the job.
        """
        jobtype = JobTypeFactory.create()
        server = JenkinsServerFactory.create()

        with mock.patch("jenkins.helpers.generate_job_name") as mock_name:
            mock_name.return_value = "known name"
            create_job(jobtype, server)

        job = Job.objects.get(jobtype=jobtype, server=server)
        self.assertEqual("known name", job.name)


@shared_task
def postbuild_testing_hook(build_pk):
    return "Testing"


class PostProcessBuildTest(TestCase):

    @override_settings(CELERY_ALWAYS_EAGER=True, POST_BUILD_TASKS=[])
    def test_postprocess_build(self):
        """
        postprocess_build should trigger the importing of the build's artifacts,
        and then schedule any other post-build tasks.
        """
        job = JobFactory.create()
        build = BuildFactory.create(job=job)
        with mock.patch("jenkins.helpers.chain") as chain_mock:
             postprocess_build(build)

        chain_mock.assert_called_once_with(
            import_build_for_job.s(build.pk))
        chain_mock.return_value.apply_async.assert_called_once()

    @override_settings(
        CELERY_ALWAYS_EAGER=True, POST_BUILD_TASKS=[postbuild_testing_hook])
    def test_postprocess_build_with_additional_postprocess_tasks(self):
        """
        If settings.POST_BUILD_TASKS has a list of additional tasks to be
        executed after a build completes, then we should chain them after we've
        imported the artifacts for the build.
        """
        job = JobFactory.create()
        build = BuildFactory.create(job=job)
        with mock.patch("jenkins.helpers.chain") as chain_mock:
            postprocess_build(build)

        chain_mock.assert_called_once_with(
            import_build_for_job.s(build.pk),
            postbuild_testing_hook.s())
        chain_mock.return_value.apply_async.assert_called_once()
