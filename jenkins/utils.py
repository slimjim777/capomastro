from urlparse import urljoin
import xml.etree.ElementTree as ET

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Template, Context
from django.utils import timezone
from django.utils.text import slugify


PARAMETERS = ".//properties/hudson.model.ParametersDefinitionProperty/parameterDefinitions/"


def get_notifications_url(base, server):
    """
    Returns the full URL for notifications given a base.
    """
    url = urljoin(base, reverse("jenkins_notifications"))
    return url + "?server=%d" % server.pk


def get_context_for_template(job, server):
    """
    Returns a Context for the Job XML templating.
    """
    defaults = DefaultSettings({"NOTIFICATION_HOST": "http://localhost"})
    url = get_notifications_url(defaults.NOTIFICATION_HOST, server)
    context_vars = {
        "notifications_url": url,
        "job": job,
        "jobtype": job.jobtype,
    }
    return Context(context_vars)


def get_job_xml_for_upload(job, server):
    """
    Return config_xml run through the template mechanism.
    """
    template = Template(job.jobtype.config_xml)
    context = get_context_for_template(job, server)
    # We need to strip leading/trailing whitespace in order to avoid having the
    # <?xml> PI not in the first line of the document.
    job_xml = template.render(context).strip()
    requestor = JenkinsParameter(
        "REQUESTOR", "The username requesting the build", "")

    job_xml = add_parameter_to_job(requestor, job_xml)
    return job_xml


def generate_job_name(jobtype):
    """
    Generates a "unique" id.
    """
    return "%s_%s" % (slugify(jobtype.name), timezone.now().strftime("%s"))


class DefaultSettings(object):
    """
    Allows easy configuration of default values for a Django settings.

    e.g. values = DefaultSettings({"NOTIFICATION_HOST": "http://example.com"})
    values.NOTIFICATION_HOST # returns the value from the default django
        settings, or the default if not provided in the settings.
    """
    class _defaults(object):
        pass

    def __init__(self, defaults):
        self.defaults = self._defaults()
        for key, value in defaults.iteritems():
            setattr(self.defaults, key, value)

    def __getattr__(self, key):
        return getattr(settings, key, getattr(self.defaults, key))

    def get_value_or_none(self, key):
        """
        Doesn't raise an AttributeError in the event that the key doesn't
        exist.
        """
        return getattr(settings, key, getattr(self.defaults, key, None))



def parse_parameters_from_job(body):
    """
    Parses the supplied XML document and extracts all parameters, returns a
    list of dictionaries with the details of the parameters extracted.
    """
    result = []
    root = ET.fromstring(body)
    for param in root.findall(PARAMETERS):
        item = {}
        for param_element in param.findall("./"):
            item[param_element.tag] = param_element.text
        result.append(item)
    return result


class JenkinsParameter(object):
    """Represents a parameter for a Jenkins job."""

    definition = "TextParameterDefinition"

    def __init__(self, name, description, default):
        self.name = name
        self.description = description
        self.default = default

    @property
    def type(self):
        return "hudson.model.%s" % self.definition


def parameter_to_xml(param):
    """
    Converts a JenkinsParameter to the XML element representation for a Jenkins
    job parameter.
    """
    element = ET.Element(param.type)
    ET.SubElement(element, "name").text = param.name
    ET.SubElement(element, "description").text = param.description
    ET.SubElement(element, "defaultValue").text = param.default
    return element


def add_parameter_to_job(param, job):
    """
    Adds a JenkinsParameter to an existing job xml document, returns the job XML
    as a string.

    # NOTE: This does nothing to check whether or not the parameter already
    # exists.
    """
    root = ET.fromstring(job)
    parameters_container = root.find(PARAMETERS[:-1])
    if parameters_container is None:
        parameters = root.find(".//hudson.model.ParametersDefinitionProperty")
        if parameters is None:
            parameters = ET.SubElement(root, "hudson.model.ParametersDefinitionProperty")
            parameters_container = ET.SubElement(parameters, "parameterDefinitions")

    parameters_container.append(parameter_to_xml(param))
    return ET.tostring(root)
