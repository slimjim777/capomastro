from django.contrib import admin

from jenkins.models import JenkinsServer, Job, Build, Artifact, JobType
from jenkins.tasks import push_job_to_jenkins


class BuildAdmin(admin.ModelAdmin):
    list_display = ("build_id", "job", "number", "phase", "status")
    list_filter = ("job", "phase", "status", "build_id")
    list_display_links = ("build_id", "job")
    search_fields = ("build_id", "job")


class JobAdmin(admin.ModelAdmin):
    actions = ['push_jobs_to_jenkins']

    def push_jobs_to_jenkins(self, request, queryset):
        for job in queryset:
            push_job_to_jenkins.delay(job.pk)
        self.message_user(request, "Jobs were pushed to Jenkins.")

    push_jobs_to_jenkins.short_description = "Push selected jobs to Jenkins"


admin.site.register(JenkinsServer)
admin.site.register(Job, JobAdmin)
admin.site.register(JobType)
admin.site.register(Build, BuildAdmin)
admin.site.register(Artifact)
