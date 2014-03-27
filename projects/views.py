from django.shortcuts import get_object_or_404
from django.views.generic import (
    CreateView, ListView, DetailView, FormView, UpdateView)
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from braces.views import (
    LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin)

from jenkins.models import Build
from projects.models import (
    Project, Dependency, ProjectDependency, ProjectBuild,
    ProjectBuildDependency)
from projects.forms import (
    ProjectForm, DependencyForm, ProjectBuildForm, ProjectBuildArchiveForm)
from projects.helpers import build_project, build_dependency
from projects.utils import get_build_table_for_project
from projects.tasks import archive_projectbuild


class ProjectCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin,
        CreateView):

    permission_required = "projects.add_project"
    form_valid_message = "Project created"
    model = Project
    form_class = ProjectForm

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class ProjectListView(LoginRequiredMixin, ListView):

    model = Project


class ProjectUpdateView(
    LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin,
        UpdateView):

    permission_required = "projects.change_project"
    form_valid_message = "Project updated"
    model = Project
    form_class = ProjectForm

    def get_success_url(self):
        return reverse("project_detail", kwargs={"pk": self.object.pk})


class InitiateProjectBuildView(LoginRequiredMixin, FormView):
    """
    Starts building a project and redirects to the newly created ProjectBuild.
    """
    form_class = ProjectBuildForm
    template_name = "projects/projectbuild_form.html"

    def get_form(self, form_class):
        """
        Returns an instance of the form to be used in this view.
        """
        project = get_object_or_404(Project, pk=self.kwargs["pk"])
        form = form_class(**self.get_form_kwargs())
        dependencies = project.dependencies
        form.fields["dependencies"].queryset = dependencies
        initial_pks = [x.pk for x in dependencies.all()]
        form.fields["dependencies"].initial = initial_pks
        form.fields["project"].initial = project
        return form

    def form_valid(self, form):
        project = form.cleaned_data["project"]
        projectbuild = build_project(
            project, user=self.request.user,
            dependencies=form.cleaned_data["dependencies"])
        messages.add_message(
            self.request, messages.INFO,
            "Build '%s' queued." % projectbuild.build_id)

        url_args = {"project_pk": project.pk, "build_pk": projectbuild.pk}
        url = reverse("project_projectbuild_detail", kwargs=url_args)
        return HttpResponseRedirect(url)


class ProjectBuildListView(LoginRequiredMixin, ListView):

    context_object_name = "projectbuilds"
    model = ProjectBuild

    def get_queryset(self):
        return ProjectBuild.objects.filter(
            project=self._get_project_from_url())

    def _get_project_from_url(self):
        return get_object_or_404(Project, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        """
        Supplement the projectbuilds with the project:
        """
        context = super(
            ProjectBuildListView, self).get_context_data(**kwargs)
        context["project"] = self._get_project_from_url()
        return context


class ProjectBuildDetailView(LoginRequiredMixin, FormView):

    form_class = ProjectBuildArchiveForm
    template_name = "projects/projectbuild_detail.html"

    def get_object(self):
        project_pk = self.kwargs["project_pk"]
        build_pk = self.kwargs["build_pk"]
        return get_object_or_404(
            ProjectBuild, project__pk=project_pk, pk=build_pk)

    def _get_project_from_url(self):
        return get_object_or_404(Project, pk=self.kwargs["project_pk"])

    def _get_build_from_url(self):
        project_pk = self.kwargs["project_pk"]
        build_pk = self.kwargs["build_pk"]
        return get_object_or_404(
            ProjectBuild, project__pk=project_pk, pk=build_pk)

    def _get_build_dependencies(self, projectbuild):
        return ProjectBuildDependency.objects.filter(projectbuild=projectbuild)

    def get_context_data(self, **kwargs):
        """
        Supplement the projectbuilds with the project:
        """
        context = super(
            ProjectBuildDetailView, self).get_context_data(**kwargs)
        context["project"] = self._get_project_from_url()
        context["projectbuild"] = self._get_build_from_url()
        context["dependencies"] = self._get_build_dependencies(
            context["projectbuild"])
        context["can_be_archived"] = context["projectbuild"].can_be_archived
        return context

    def form_valid(self, form):
        """
        Queue archiving of this project build.
        """
        projectbuild = self.get_object()
        archive = form.cleaned_data["archive"]
        # TODO: See note in helpers about refactoring the tasks/helpers.
        archive_projectbuild.delay(projectbuild.pk, archive.pk)
        messages.add_message(
            self.request, messages.INFO,
            "Archiving for '%s' queued." % projectbuild.build_id)
        url = reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": projectbuild.project.pk,
                    "build_pk": projectbuild.pk})
        return HttpResponseRedirect(url)


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
        context["projectbuilds"] = ProjectBuild.objects.filter(
            project=context["project"])[:5]
        return context


class DependencyCreateView(
    LoginRequiredMixin, PermissionRequiredMixin, FormValidMessageMixin,
        CreateView):

    permission_required = "projects.add_dependency"
    form_valid_message = "Dependency created"
    form_class = DependencyForm
    model = Dependency

    def get_success_url(self):
        url_args = {"pk": self.object.pk}
        return reverse("dependency_detail", kwargs=url_args)


class DependencyListView(LoginRequiredMixin, ListView):

    context_object_name = "dependencies"
    model = Dependency


class DependencyDetailView(LoginRequiredMixin, DetailView):

    context_object_name = "dependency"
    model = Dependency

    def get_context_data(self, **kwargs):
        """
        Supplement the dependency.
        """
        context = super(
            DependencyDetailView, self).get_context_data(**kwargs)
        context["builds"] = Build.objects.filter(
            job=context["dependency"].job)
        context["projects"] = Project.objects.filter(
            dependencies=context["dependency"])
        return context

    def post(self, request, pk):
        """
        Queue a build of this Dependency.
        """
        dependency = get_object_or_404(Dependency, pk=pk)
        build_dependency(dependency)
        messages.add_message(
            self.request, messages.INFO,
            "Build for '%s' queued." % dependency.name)
        url = reverse("dependency_detail", kwargs={"pk": dependency.pk})
        return HttpResponseRedirect(url)


class ProjectDependenciesView(LoginRequiredMixin, DetailView):

    model = Project
    context_object_name = "project"
    template_name = "projects/project_dependencies.html"

    def _get_builds_for_dependency(self, projectdependency):
        """
        Return the builds for a project dependency.
        """
        return Build.objects.filter(job=projectdependency.dependency.job)

    def get_context_data(self, **kwargs):
        """
        Supplement the project with its dependencies.
        """
        context = super(
            ProjectDependenciesView, self).get_context_data(**kwargs)
        header, table = get_build_table_for_project(context["project"])
        context["builds_header"] = header
        context["builds_table"] = table
        return context


__all__ = [
    "ProjectCreateView", "ProjectListView", "ProjectDetailView",
    "DependencyCreateView", "InitiateProjectBuildView", "ProjectBuildListView",
    "ProjectBuildDetailView", "DependencyListView", "DependencyDetailView",
    "ProjectUpdateView", "ProjectDependenciesView"
]
