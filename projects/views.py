from django.shortcuts import get_object_or_404
from django.views.generic import CreateView, ListView, DetailView, View
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from braces.views import (
    LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin,
    SuccessURLRedirectListMixin)

from jenkins.models import Build
from projects.models import Project, Dependency, ProjectDependency, ProjectBuild
from projects.forms import ProjectForm
from projects.helpers import build_project


class ProjectCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessURLRedirectListMixin, FormValidMessageMixin, CreateView):

    permission_required = "projects.add_project"
    success_list_url = "projects_index"
    form_valid_message = "Project created"
    model = Project
    form_class = ProjectForm


class ProjectListView(LoginRequiredMixin, ListView):

    model = Project


class InitiateProjectBuildView(LoginRequiredMixin, View):

    def post(self, request, pk):
        project = Project.objects.get(pk=pk)
        project_build = build_project(project)
        messages.add_message(
            request, messages.INFO, "Build '%s' Queued." % project_build.build_id)
        return HttpResponseRedirect(reverse("projects_index"))


class ProjectBuildListView(LoginRequiredMixin, ListView):

    context_object_name = "project_builds"
    model = ProjectBuild

    def get_queryset(self):
        return ProjectBuild.objects.filter(project=self._get_project_from_url())

    def _get_project_from_url(self):
        return get_object_or_404(Project, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        """
        Supplement the project_builds with the project:
        """
        context = super(
            ProjectBuildListView, self).get_context_data(**kwargs)
        context["project"] = self._get_project_from_url()
        return context



class ProjectBuildDetailView(LoginRequiredMixin, DetailView):

    context_object_name = "project_build"
    model = ProjectBuild

    def get_object(self):
        return get_object_or_404(ProjectBuild,
            project__pk=self.kwargs["project_pk"], pk=self.kwargs["build_pk"])

    def _get_project_from_url(self):
        return get_object_or_404(Project, pk=self.kwargs["project_pk"])

    def _get_related_builds(self, project_build):
        return Build.objects.filter(build_id=project_build.build_id)

    def get_context_data(self, **kwargs):
        """
        Supplement the project_builds with the project:
        """
        context = super(
            ProjectBuildDetailView, self).get_context_data(**kwargs)
        context["project"] = self._get_project_from_url()
        context["builds"] = self._get_related_builds(context["project_build"])
        return context


class ProjectDetailView(LoginRequiredMixin, DetailView):

    model = Project
    context_object_name = "project"

    def get_context_data(self, **kwargs):
        """
        Supplement the project with its dependencies.
        """
        context = super(
            ProjectDetailView, self).get_context_data(**kwargs)
        context["dependencies"] = ProjectDependency.objects.filter(
            project=context["project"])
        return context


class DependencyCreateView(
    LoginRequiredMixin, PermissionRequiredMixin,
    SuccessURLRedirectListMixin, FormValidMessageMixin, CreateView):

    model = Dependency
    fields = ["name", "dependency_type"]


__all__ = [
    "ProjectCreateView", "ProjectListView", "ProjectDetailView", 
    "DependencyCreateView", "InitiateProjectBuildView", "ProjectBuildListView",
    "ProjectBuildDetailView"
]
