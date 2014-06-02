from django.shortcuts import get_object_or_404

from rest_framework import viewsets, routers, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from jenkins.models import JenkinsServer, Job, JobType, Build, Artifact
from projects.models import Project, Dependency
from projects.helpers import build_dependency


class JenkinsServerViewSet(viewsets.ModelViewSet):
    model = JenkinsServer


class JobViewSet(viewsets.ModelViewSet):
    model = Job


class JobTypeSerializer(serializers.ModelSerializer):

    parameters = serializers.SerializerMethodField("get_parameters")

    class Meta:
        model = JobType

    def get_parameters(self, obj):
          return obj.get_parameters()


class JobTypeViewSet(viewsets.ModelViewSet):
    model = JobType
    serializer_class = JobTypeSerializer


class BuildViewSet(viewsets.ModelViewSet):
    model = Build


class ArtifactViewSet(viewsets.ModelViewSet):
    model = Artifact


class ProjectViewSet(viewsets.ModelViewSet):
    model = Project


class DependencyViewSet(viewsets.ModelViewSet):
    model = Dependency

    @action(permission_classes=[IsAuthenticated])
    def build_dependency(self, request, pk=None):
        """
        We can request the build of a dependency through the API.

        TODO: Should we return a different HTTP Code if we are already building
        and don't start a new build?
        """
        dependency = get_object_or_404(Dependency, pk=pk)
        if not dependency.is_building:
            build_dependency(dependency)
        return Response("", status=202)

router = routers.DefaultRouter()
router.register(r"servers", JenkinsServerViewSet)
router.register(r"jobs", JobViewSet)
router.register(r"jobtypes", JobTypeViewSet)
router.register(r"builds", BuildViewSet)
router.register(r"artifacts", ArtifactViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"dependencies", DependencyViewSet)
