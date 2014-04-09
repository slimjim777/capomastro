import codecs
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from jenkins.management.helpers import import_jobtype


class Command(BaseCommand):
    help = "Import jobtype from config.xml"
    args = "[jobtype] [config.xml]"

    option_list = BaseCommand.option_list + (
        make_option(
            "--update", action="store_true", dest="update",
            default=False, help="Update if job type already exists."),
    )

    def handle(self, *args, **options):
        if len(args) != 2:
            raise CommandError("must provide a config.xml and jobtype")
        jobtype, filename = args

        with codecs.open(filename) as f:
            import_jobtype(
                jobtype, f, update=options["update"], stdout=self.stdout)

        transaction.commit_unless_managed()
