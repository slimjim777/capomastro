from rest_framework import viewsets, routers, serializers

from jenkins.models import JenkinsServer, Job, JobType, Build, Artifact
from projects.models import Project, Dependency


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


router = routers.DefaultRouter()
router.register(r"servers", JenkinsServerViewSet)
router.register(r"jobs", JobViewSet)
router.register(r"jobtypes", JobTypeViewSet)
router.register(r"builds", BuildViewSet)
router.register(r"artifacts", ArtifactViewSet)
router.register(r"projects", ProjectViewSet)
router.register(r"dependencies", DependencyViewSet)
