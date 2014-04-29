from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from django.test.utils import override_settings

import mock

from jenkins.utils import (
    get_notifications_url, DefaultSettings, get_job_xml_for_upload,
    get_context_for_template, generate_job_name)
from .factories import JobFactory, JobTypeFactory, JenkinsServerFactory


class NotificationUrlTest(SimpleTestCase):

    def test_get_notifications_url(self):
        """
        get_notifications_url should reverse the notification url and return a
        complete HTTP URL from the base provided.
        """
        server = JenkinsServerFactory.create()
        self.assertEqual(
            "http://example.com/jenkins/notifications/?server=%d" % server.pk,
            get_notifications_url("http://example.com/", server))


class DefaultSettingsTest(SimpleTestCase):

    def test_default_values(self):
        """
        Anything we put in the configuration is available as a property on the
        settings object.
        """
        settings = DefaultSettings({"SERVER_HOST": "testing"})
        self.assertEqual("testing", settings.SERVER_HOST)

    def test_missing_value(self):
        """
        We should get an attribute error if there is no setting for a value.
        """
        settings = DefaultSettings({})
        with self.assertRaises(AttributeError) as cm:
            settings.MY_UNKNOWN_VALUE

        self.assertEqual(
            "'_defaults' object has no attribute 'MY_UNKNOWN_VALUE'",
            str(cm.exception))

    def test_get_value_or_none(self):
        """
        DefaultSettings.get_value_or_none should return None if there is no
        value or if it's None.
        """
        settings = DefaultSettings({"MY_VALUE": None})

        self.assertIsNone(settings.get_value_or_none("MY_TEST_VALUE"))
        self.assertIsNone(settings.get_value_or_none("MY_VALUE"))


class GetContextForTemplate(TestCase):

    @override_settings(NOTIFICATION_HOST="http://example.com")
    def test_get_context_for_template(self):
        """
        get_context_for_template should return a Context object with details
        from the job and anywhere else to be used when templating the job
        config.xml.
        """
        job = JobFactory.create()
        server = JenkinsServerFactory.create()
        context = get_context_for_template(job, server)

        self.assertEqual(job, context.get("job"))
        self.assertEqual(
            "http://example.com/jenkins/notifications/?server=%d" % server.pk,
            context.get("notifications_url"))

template_config = """
<?xml version='1.0' encoding='UTF-8'?>
<project>
  <actions/>
  <description>{{ jobtype.description }}</description>
  <keepDependencies>false</keepDependencies>
  <properties>
    <com.tikal.hudson.plugins.notification.HudsonNotificationProperty plugin="notification@1.5">
      <endpoints>
        <com.tikal.hudson.plugins.notification.Endpoint>
          <protocol>HTTP</protocol>
          <format>JSON</format>
          <url>{{ notifications_url }}</url>
        </com.tikal.hudson.plugins.notification.Endpoint>
      </endpoints>
    </com.tikal.hudson.plugins.notification.HudsonNotificationProperty>
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.TextParameterDefinition>
          <name>BUILD_ID</name>
          <description></description>
          <defaultValue></defaultValue>
        </hudson.model.TextParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
</project>
"""


class GetTemplatedJobTest(TestCase):

    # TODO: How much verification of Job XML documents should we do?

    @override_settings(NOTIFICATION_HOST="http://example.com")
    def test_get_job_xml_for_upload(self):
        """
        get_job_xml_for_upload should take a job and return the XML that needs
        to be uploaded to build the job.
        """
        jobtype = JobTypeFactory.create(config_xml=template_config)
        job = JobFactory.create(jobtype=jobtype)
        server = JenkinsServerFactory.create()
        xml_for_upload = get_job_xml_for_upload(job, server)
        expected_url = get_notifications_url("http://example.com/", server)
        self.assertIn(job.jobtype.description, xml_for_upload)
        self.assertIn(expected_url, xml_for_upload)

    def test_get_job_xml_for_upload_strips_leading_spaces(self):
        """
        If we attempt to upload an XML document that has leading whitespace,
        then Jenkins will fail with a weird error.

        "processing instruction can not have PITarget with reserveld xml"
        """
        server = JenkinsServerFactory.create()
        jobtype = JobTypeFactory.create(config_xml="\ntesting")
        job = JobFactory.create(jobtype=jobtype)
        self.assertEqual("testing", get_job_xml_for_upload(job, server))


class GenerateNameJobTest(TestCase):

    def test_generate_job_name(self):
        """
        generate_job_name should generate a name for the job on the server when
        given a jobtype.
        """
        job = JobFactory.create(name=u"My Test Job")
        now = timezone.now()

        with mock.patch("jenkins.utils.timezone") as timezone_mock:
            timezone_mock.now.return_value = now
            name = generate_job_name(job)
        expected_job_name = u"my-test-job_%s" % now.strftime("%s")
        self.assertEqual(name, expected_job_name)


class GetAuthenticatedArtifactUrlTest(TestCase):

    def test_get_authenticated_artifact_url(self):
        """
        Returns a url with username:password embedded to make it easier to
        provide links to download artifacts direct from the UI.
        """

