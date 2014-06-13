from django.test import TestCase
from django.test.utils import override_settings

import mock
import jenkinsapi

from jenkins.models import Build
from jenkins.tasks import (
    build_job, push_job_to_jenkins, import_build_for_job,
    delete_job_from_jenkins)
from .factories import (
    JobFactory, JenkinsServerFactory, JobTypeFactory, BuildFactory)


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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
            build_job(job.pk, "20140312.1", params={"MYTEST": "500"})

        mock_jenkins.assert_called_with(
            self.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.build_job.assert_called_with(
            job.name, params={"MYTEST": "500", "BUILD_ID": "20140312.1"})


class ImportBuildTaskTest(TestCase):

    @override_settings(
        CELERY_ALWAYS_EAGER=True, NOTIFICATION_HOST="http://example.com")
    def test_import_build_for_job(self):
        """
        Import build for job should update the build with the details fetched
        from the Jenkins server, including fetching the artifact details.
        """
        job = JobFactory.create()
        build = BuildFactory.create(job=job, number=5)

        mock_job = mock.Mock(spec=jenkinsapi.job.Job)
        mock_build = mock.Mock(_data={"duration": 1000})

        mock_job.get_build.return_value = mock_build

        mock_build.get_status.return_value = "SUCCESS"
        mock_build.get_result_url.return_value = "http://localhost/123"
        mock_build.get_console.return_value = "This is the log"
        mock_build.get_artifacts.return_value = []
        parameters = [{"name": "BUILD_ID", "value": ""}]
        mock_build.get_actions.return_value = {"parameters": parameters}

        with mock.patch("jenkins.tasks.logger") as mock_logger:
            with mock.patch("jenkins.models.Jenkins") as mock_jenkins:
                mock_jenkins.return_value.get_job.return_value = mock_job
                result = import_build_for_job(build.pk)

        self.assertEqual(build.pk, result)
        mock_jenkins.assert_called_with(
            job.server.url, username=u"root", password=u"testing")

        mock_logger.assert_has_calls(
            [mock.call.info("Located job %s\n" % job),
             mock.call.info("Using server at %s\n" % job.server.url),
             mock.call.info("Processing build details for %s #5" % job)])

        build = Build.objects.get(pk=build.pk)
        self.assertEqual(1000, build.duration)
        self.assertEqual("SUCCESS", build.status)
        self.assertEqual("This is the log", build.console_log)
        self.assertEqual(parameters, build.parameters)


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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
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
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
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


class RemoveJobTaskTest(TestCase):

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_delete_job_from_jenkins(self):
        """
        The delete_job_from_jenkins task should remove the job from the correct
        server.
        """
        jobtype = JobTypeFactory.create(config_xml=job_xml)
        job = JobFactory.create(jobtype=jobtype, name="testing")
        with mock.patch(
                "jenkins.models.Jenkins",
                spec=jenkinsapi.jenkins.Jenkins) as mock_jenkins:
            mock_jenkins.return_value.has_job.return_value = True
            delete_job_from_jenkins(job.pk)

        mock_jenkins.assert_called_with(
            job.server.url, username=u"root", password=u"testing")
        mock_jenkins.return_value.delete_job.assert_called_with("testing")
