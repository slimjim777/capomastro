from __future__ import unicode_literals
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from jenkins.management.helpers import import_jenkinsserver


# TODO: implement optional field updating...

class Command(BaseCommand):
    help = "Import or update a JenkinsServer"
    args = "[name] [url] [username] [password]"

    option_list = BaseCommand.option_list + (
        make_option(
            "--update", action="store_true", dest="update",
            default=False, help="Update if server already exists."),
    )

    def handle(self, *args, **options):
        if len(args) != 4:
            raise CommandError("must provide all parameters")
        name, url, username, password = args

        import_jenkinsserver(
            name, url, username, password, update=options["update"],
            stdout=self.stdout)

        transaction.commit_unless_managed()
