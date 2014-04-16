from django.contrib import admin

from projects.models import (
    Dependency, Project, ProjectBuild, ProjectBuildDependency)


class ProjectDependencyInline(admin.TabularInline):
    model = Project.dependencies.through


class ProjectAdmin(admin.ModelAdmin):
    inlines = [ProjectDependencyInline]


class ProjectBuildDependencyInline(admin.TabularInline):
    model = ProjectBuild.build_dependencies.through


class ProjectBuildAdmin(admin.ModelAdmin):
    inlines = [ProjectBuildDependencyInline]


admin.site.register(Dependency)
admin.site.register(Project, ProjectAdmin)


admin.site.register(ProjectBuildDependency)
admin.site.register(ProjectBuild, ProjectBuildAdmin)
