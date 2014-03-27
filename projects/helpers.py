from django.utils import timezone

from jenkins.tasks import build_job
from projects.models import ProjectDependency


def build_dependency(dependency, build_id=None):
    """
    Queues a build of the job associated with the depenency along with
    any parameters that might be needed.
    """
    build_parameters = dependency.get_build_parameters()
    kwargs = {}
    if build_parameters:
        kwargs["params"] = build_parameters
    if build_id:
        kwargs["build_id"] = build_id
    build_job.delay(
        dependency.job.pk, **kwargs)


def build_project(project, user=None, dependencies=None, queue_build=True):
    """
    Given a build, schedule building each of its dependencies.
    """
    dependencies = dependencies and dependencies or []
    from projects.models import ProjectBuild, ProjectBuildDependency
    build = ProjectBuild.objects.create(
        project=project, requested_by=user)

    if dependencies:
        filter_args = {"dependency__in": dependencies}
    else:
        filter_args = {}

    dependencies_to_build = ProjectDependency.objects.filter(
        project=project, **filter_args)
    dependencies_not_to_build = ProjectDependency.objects.filter(
        project=project).exclude(pk__in=dependencies_to_build)

    for dependency in dependencies_to_build.order_by("dependency__job__pk"):
        kwargs = {"projectbuild": build,
                  "dependency": dependency.dependency}
        ProjectBuildDependency.objects.create(**kwargs)
        if queue_build:
            build_dependency(dependency.dependency, build_id=build.build_id)

    for dependency in dependencies_not_to_build:
        kwargs = {"projectbuild": build,
                  "dependency": dependency.dependency,
                  "build": dependency.current_build}
        ProjectBuildDependency.objects.create(**kwargs)
    return build


def get_transport_for_projectbuild(projectbuild, archive):
    """
    Returns a transport for a projectbuild to be archived to a specific
    archive.
    """
    policy = archive.get_policy()(projectbuild)
    transport = archive.get_archiver()(policy, archive)
    return transport


# TODO: It'd be nice if this handled the task, so that a view didn't need to
# know whether or not there was a delayed task involved.
def archive_projectbuild(projectbuild, archive):
    """
    Archives the artifacts for a projectbuild.

    Requires a projectbuild and a destination archive.
    """
    transport = get_transport_for_projectbuild(projectbuild, archive)
    transport.archive()
    projectbuild.archived = timezone.now()
    projectbuild.save()
