from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from jenkins.models import JobType
from jenkins.tests.fixtures import job_with_parameters
from jenkins.tests.factories import JobTypeFactory


class JobTypeAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_jobtype_parameters(self):
        """
        The JobType resource should expose the parameters.
        """
        self.client.force_authenticate(user=self.user)
        job_type = JobTypeFactory.create(config_xml=job_with_parameters)

        url = reverse("jobtype-list")
        response = self.client.get(url)

        self.assertEqual(1, len(response.data))
        self.assertEqual(job_type.name, response.data[0]["name"])

        self.assertEqual(
            job_type.get_parameters(),
            response.data[0]["parameters"])
