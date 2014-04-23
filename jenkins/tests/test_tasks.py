from django.test import TestCase
from django.test.utils import override_settings

import mock
from jenkinsapi import jenkins

from jenkins.tasks import build_job, push_job_to_jenkins, import_build
from .factories import (
    JobFactory, JenkinsServerFactory, JobTypeFactory)


class BuildJobTaskTest(TestCase):

    def setUp(self):
        self.server = JenkinsServerFactory.create()

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_build_job(self):
        """
        The build_job task should find the associated server, and request that
        the job be built.
        """
        job = JobFactory.create(server=self.server)
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            build_job(job.pk)

        mock_jenkins.assert_called_with(
            self.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.build_job.assert_called_with(
            job.name, params={})

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_build_job_with_build_id(self):
        """
        If we provide a build_id, this should be sent as parameter.
        """
        job = JobFactory.create(server=self.server)
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            build_job(job.pk, "20140312.1")

        mock_jenkins.assert_called_with(
            self.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.build_job.assert_called_with(
            job.name, params={"BUILD_ID": "20140312.1"})

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_build_job_with_params(self):
        """
        If we provide parameters, then they should be passed with the job build
        request.
        """
        job = JobFactory.create(server=self.server)
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            build_job(job.pk, params={"MYTEST": "500"})

        mock_jenkins.assert_called_with(
            self.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.build_job.assert_called_with(
            job.name, params={"MYTEST": "500"})

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_build_job_with_params_and_build_id(self):
        """
        If we provide parameters and a build_id, we should get both in the
        parameters.
        """
        job = JobFactory.create(server=self.server)
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            build_job(job.pk, "20140312.1", params={"MYTEST": "500"})

        mock_jenkins.assert_called_with(
            self.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.build_job.assert_called_with(
            job.name, params={"MYTEST": "500", "BUILD_ID": "20140312.1"})


class ImportBuildTaskTest(TestCase):

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_import_build(self):
        """
        import_build should pull the details for the build and create artifacts
        for them.
        """
        job = JobFactory.create()
        with mock.patch("jenkins.tasks.import_build_for_job") as task_mock:
            import_build.delay(job.pk, 5)

        task_mock.assert_called_once_with(job.pk, 5)


job_xml = """
<?xml version='1.0' encoding='UTF-8'?>
<project>{{ notifications_url }}</project>
"""


class CreateJobTaskTest(TestCase):

    @override_settings(
        CELERY_ALWAYS_EAGER=True, NOTIFICATION_HOST="http://example.com")
    def test_push_job_to_jenkins(self):
        """
        The push_job_to_jenkins task should find the associated server, and
        create the job with the right name and content.
        """
        jobtype = JobTypeFactory.create(config_xml=job_xml)
        job = JobFactory.create(jobtype=jobtype, name="testing")
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            mock_jenkins.return_value.has_job.return_value = False
            push_job_to_jenkins(job.pk)

        mock_jenkins.assert_called_with(
            job.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.has_job.assert_called_with("testing")
        mock_jenkins.return_value.create_job.assert_called_with(
            "testing",
            job_xml.replace(
                "{{ notifications_url }}",
                "http://example.com/jenkins/notifications/?server=%d" %
                job.server.pk).strip())

    @override_settings(
        CELERY_ALWAYS_EAGER=True, NOTIFICATION_HOST="http://example.com")
    def test_push_job_to_jenkins_with_already_existing_job(self):
        """
        If the jobname specified already exists in Jenkins, then we can assume
        we're updating the Job's config.xml.
        """
        jobtype = JobTypeFactory.create(config_xml=job_xml)
        job = JobFactory.create(jobtype=jobtype, name="testing")
        mock_apijob = mock.Mock()

        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkins.Jenkins) as mock_jenkins:
            mock_jenkins.return_value.has_job.return_value = True
            mock_jenkins.return_value.get_job.return_value = mock_apijob
            push_job_to_jenkins(job.pk)

        mock_jenkins.assert_called_with(
            job.server.url, username=u"root", password=u"testing")

        mock_jenkins.return_value.has_job.assert_called_with("testing")
        mock_apijob.update_config.assert_called_with(
            job_xml.replace(
                "{{ notifications_url }}",
                "http://example.com/jenkins/notifications/?server=%d" %
                job.server.pk).strip())
