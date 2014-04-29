import factory
import factory.fuzzy

from jenkins.models import Build, Job, JenkinsServer, Artifact, JobType


class JenkinsServerFactory(factory.DjangoModelFactory):
    FACTORY_FOR = JenkinsServer

    name = factory.Sequence(lambda n: "Server %d" % n)
    url = factory.Sequence(lambda n: "http://www%d.example.com/" % n)
    username = "root"
    password = "testing"


class JobTypeFactory(factory.DjangoModelFactory):
    FACTORY_FOR = JobType

    name = factory.Sequence(lambda n: "type%d" % n)
    description = "This is a dependency type."
    config_xml = "<?xml version='1.0' encoding='UTF-8'?><project></project>"


class JobFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Job

    server = factory.SubFactory(JenkinsServerFactory)
    jobtype = factory.SubFactory(JobTypeFactory)
    name = factory.Sequence(lambda n: "job_%d" % n)


class BuildFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Build

    job = factory.SubFactory(JobFactory)
    build_id = factory.fuzzy.FuzzyText(length=12)
    number = factory.Sequence(lambda n: n)
    duration = factory.fuzzy.FuzzyInteger(100, 500000)
    status = "SUCCESS"
    phase = "STARTED"
    url = factory.Sequence(lambda n: "http://www.example.com/job/%d" % n)


class ArtifactFactory(factory.DjangoModelFactory):
    FACTORY_FOR = Artifact

    build = factory.SubFactory(BuildFactory)
    filename = factory.fuzzy.FuzzyText(length=20)
    url = factory.Sequence(lambda n: "http://example.com/file/%d" % n)
