from django.template.base import Library
from django.core.urlresolvers import reverse

from projects.models import ProjectBuild


register = Library()


@register.simple_tag()
def build_url(build_key):
    """
    Fetches the ProjectBuild for a given build_id, if any.
    """
    try:
        build = ProjectBuild.objects.get(build_key=build_key)
        return reverse(
            "project_projectbuild_detail",
            kwargs={"project_pk": build.project.pk, "build_pk": build.pk})
    except ProjectBuild.DoesNotExist:
        return ""
