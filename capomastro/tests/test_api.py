from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from rest_framework.test import APITestCase

from jenkins.tests.factories import JobTypeWithParamsFactory


class JobTypeAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_jobtype_parameters(self):
        """
        The JobType resource should expose the parameters.
        """
        self.client.force_authenticate(user=self.user)
        job_type = JobTypeWithParamsFactory.create()

        url = reverse("jobtype-list")
        response = self.client.get(url)

        self.assertEqual(1, len(response.data))
        self.assertEqual(job_type.name, response.data[0]["name"])

        self.assertEqual(
            job_type.get_parameters(),
            response.data[0]["parameters"])
