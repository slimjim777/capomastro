from django.contrib import admin

from jenkins.models import JenkinsServer, Job, Build, Artifact, JobType


class BuildAdmin(admin.ModelAdmin):
    list_display = ("build_id", "job", "number", "phase", "status")
    list_filter = ("job", "phase", "status", "build_id")
    list_display_links = ("build_id", "job")
    search_fields = ("build_id", "job")


admin.site.register(JenkinsServer)
admin.site.register(Job)
admin.site.register(JobType)
admin.site.register(Build, BuildAdmin)
admin.site.register(Artifact)
