from django.test import TestCase

from httmock import HTTMock
from jenkinsapi.jenkins import Jenkins

from jenkins.models import Build, JobType
from .helpers import mock_url
from .factories import (
    BuildFactory, JenkinsServerFactory, JobTypeWithParamsFactory)


class JenkinsServerTest(TestCase):

    def test_get_client(self):
        """
        JenkinsServer.get_client should return a Jenkins client configured
        appropriately.
        """
        server = JenkinsServerFactory.create()

        mock_request = mock_url(
            r"\/api\/python$", "fixture1")
        with HTTMock(mock_request):
            client = server.get_client()
        self.assertIsInstance(client, Jenkins)


class BuildTest(TestCase):

    def test_ordering(self):
        """Builds should be ordered in reverse build order by default."""
        builds = BuildFactory.create_batch(5)
        build_numbers = sorted([x.number for x in builds], reverse=True)

        self.assertEqual(
            build_numbers,
            list(Build.objects.all().values_list("number", flat=True)))


class JobTypeTest(TestCase):

    def test_instantiation(self):
        """We can create JobTypes."""
        JobType.objects.create(
            name="my-test", config_xml="testing xml")

    def test_get_parameters(self):
        """
        JobType.get_parameters should use the parameter parsing to fetch the
        correct parameters.
        """
        job_type = JobTypeWithParamsFactory.create()
        parameters = job_type.get_parameters()
        self.assertEqual(
            ["BUILD_ID", "BRANCH_TO_CHECKOUT"],
            [x["name"] for x in parameters])
