from django.core.urlresolvers import reverse
from django.contrib.auth.models import User, Permission

from rest_framework import status
from rest_framework.test import APITestCase

import mock

from jenkins.tests.factories import JobTypeWithParamsFactory, BuildFactory
from projects.tests.factories import DependencyFactory


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


class DependencyBuildAPITest(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user("testing")

    def test_build_dependency(self):
        """
        We can build a dependency through the API.
        """
        self.client.force_authenticate(user=self.user)
        dependency = DependencyFactory.create()

        url = reverse("dependency-build-dependency", kwargs={"pk": dependency.pk})

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = self.client.post(url)

        self.assertEqual(status.HTTP_202_ACCEPTED, response.status_code)
        build_job_mock.delay.assert_called_once_with(
            dependency.job.pk)

    def test_build_dependency_already_building(self):
        """
        If the Dependency appears to be already building, then we should 
        """
        self.client.force_authenticate(user=self.user)
        dependency = DependencyFactory.create()
        BuildFactory.create(job=dependency.job)

        url = reverse("dependency-build-dependency", kwargs={"pk": dependency.pk})

        with mock.patch("projects.helpers.build_job") as build_job_mock:
            response = self.client.post(url)

        self.assertEqual(status.HTTP_202_ACCEPTED, response.status_code)
        self.assertFalse(build_job_mock.delay.called)
