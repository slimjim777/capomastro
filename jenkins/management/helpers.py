from django.core.management.base import CommandError
from requests.exceptions import HTTPError

from jenkins.models import JobType, JenkinsServer


REQUIRED_PLUGINS = ["notification"]


def verify_jenkinsserver(server):
    """
    Perform some perfunctory tests to check if a server is suitable for use
    with Capomastro.
    """
    messages = []
    try:
        client = server.get_client()
    except HTTPError as e:
        messages.append("ERROR: %s" % str(e))
    else:
        plugins = client.get_plugins()
        missing_plugins = []
        for plugin in REQUIRED_PLUGINS:
            if not plugin in plugins:
                missing_plugins.append(plugin)
        if missing_plugins:
            messages.append("Missing plugins: " + ",".join(missing_plugins))
    return messages


def import_jobtype(jobtype, jobfile, update=False, stdout=None):
    """
    Import or update content to the specified jobtype.
    """
    content = jobfile.read()
    try:
        existing = JobType.objects.get(name=jobtype)
        if update:
            existing.config_xml = content
            existing.save()
            if stdout:
                stdout.write("Jobtype updated\n")
        else:
            raise CommandError("Jobtype already exists")
    except JobType.DoesNotExist:
        JobType.objects.create(name=jobtype, config_xml=content)
        if stdout:
            stdout.write("Jobtype created\n")


def import_jenkinsserver(
        name, url, username, password, update=False, stdout=None):
    """
    Create a JenkinsServer or update the details.
    """
    try:
        existing = JenkinsServer.objects.get(name=name)
        if update:
            existing.url = url
            existing.username = username
            existing.password = password
            existing.save()
            if stdout:
                stdout.write("Server updated\n")
        else:
            raise CommandError("Server already exists")
    except JenkinsServer.DoesNotExist:
        JenkinsServer.objects.create(
            name=name, url=url, username=username, password=password)
        if stdout:
            stdout.write("Server created\n")
