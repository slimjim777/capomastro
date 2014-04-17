import json
import logging

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View, ListView, DetailView, TemplateView
from braces.views import LoginRequiredMixin, CsrfExemptMixin

from jenkins.models import JenkinsServer, Build, Job, JobType
from jenkins.tasks import import_build


class NotificationHandlerView(CsrfExemptMixin, View):

    http_method_names = ["post"]

    def get_server(self, request):
        """
        Attempt to locate the remote server for this request.
        """
        remote_addr = request.META["REMOTE_ADDR"]
        try:
            return JenkinsServer.objects.get(remote_addr=remote_addr)
        except JenkinsServer.DoesNotExist:
            logging.warn(
                "Could not find server with REMOTE_ADDR: %s" % remote_addr)

    def post(self, request, *args, **kwargs):
        """
        Handle incoming Jenkins notifications.
        """
        server = self.get_server(request)
        if not server:
            return HttpResponse(status=412)
        notification = json.loads(request.body)

        try:
            job = server.job_set.get(name=notification["name"])
        except Job.DoesNotExist:
            logging.warn(
                "Notification for unknown job '%s'" % notification["name"])
            return HttpResponse(status=412)

        build_id = ""
        build_number = notification["build"]["number"]
        build_phase = notification["build"]["phase"]
        if "parameters" in notification["build"]:
            build_id = notification["build"]["parameters"].get("BUILD_ID")

        if notification["build"]["phase"] == "STARTED":
            job.build_set.create(
                number=build_number, build_id=build_id, phase=build_phase)
        elif notification["build"]["phase"] == "FINISHED":
            build_status = notification["build"]["status"]
            build_url = notification["build"]["url"]
            try:
                existing_build = job.build_set.get(number=build_number)
            except Build.DoesNotExist:
                job.build_set.create(
                    number=build_number, build_id=build_id, phase=build_phase,
                    status=build_status, url=build_url)
            else:
                existing_build.status = build_status
                existing_build.phase = build_phase
                existing_build.url = build_url
                existing_build.save()

            import_build.delay(job.pk, build_number)
        return HttpResponse(status=200)


class JenkinsServerListView(LoginRequiredMixin, ListView):

    model = JenkinsServer


class JenkinsServerDetailView(LoginRequiredMixin, DetailView):

    model = JenkinsServer
    context_object_name = "server"

    def get_context_data(self, **kwargs):
        """
        Supplement the server with the jobs for this server.
        """
        context = super(
            JenkinsServerDetailView, self).get_context_data(**kwargs)
        context["jobs"] = context["server"].job_set.all()
        return context


class JenkinsServerJobBuildsIndexView(LoginRequiredMixin, TemplateView):

    template_name = "jenkins/jenkinsserver_job_builds_index.html"

    def get_context_data(self, **kwargs):
        context = super(
            JenkinsServerJobBuildsIndexView, self).get_context_data(**kwargs)
        server = get_object_or_404(JenkinsServer, pk=kwargs["server_pk"])
        job = get_object_or_404(server.job_set, pk=kwargs["job_pk"])
        context["builds"] = job.build_set.all()
        context["job"] = job
        context["server"] = server
        return context


class JobTypeDetailView(LoginRequiredMixin, DetailView):

    model = JobType
    context_object_name = "jobtype"


class BuildDetailView(LoginRequiredMixin, DetailView):

    model = Build
    context_object_name = "build"

    def get_context_data(self, **kwargs):
        """
        Supplement the server with the jobs for this server.
        """
        context = super(
            BuildDetailView, self).get_context_data(**kwargs)
        return context


__all__ = [
    "NotificationHandlerView", "JenkinsServerListView",
    "JenkinsServerDetailView", "JenkinsServerJobBuildsIndexView",
    "JobTypeDetailView", "BuildDetailView"]
