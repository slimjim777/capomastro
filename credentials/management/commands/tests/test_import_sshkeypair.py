from __future__ import unicode_literals

from cStringIO import StringIO
from tempfile import mkstemp
import os

from django.test import TestCase
from django.core.management.base import CommandError

from credentials.management.commands.import_sshkeypair import (
    Command)
from credentials.models import SshKeyPair


class ImportSshKeytTest(TestCase):

    def setUp(self):
        self.public = self.create_temp_file("public key")
        self.private = self.create_temp_file("private key")

    def tearDown(self):
        os.unlink(self.public)
        os.unlink(self.private)

    def create_temp_file(self, content):
        fd, path = mkstemp()
        os.write(fd, content)
        os.close(fd)
        return path

    def test_run_command_with_key_import(self):
        """
        Running the import_sshkeypair command with the correct details should
        result in the keypair being imported.
        """
        command = Command()
        command.execute(
            self.public, self.private, "testing", stdout=StringIO(),
            update=False)

        self.assertEqual("Key pair created\n", command.stdout.getvalue())
        self.assertEqual(1, SshKeyPair.objects.count())
        keypair = SshKeyPair.objects.get(label="testing")
        self.assertEqual("public key", keypair.public_key)
        self.assertEqual("private key", keypair.private_key)

    def test_run_command_with_missing_parameter(self):
        """
        If we miss a parameter then we should get an appropriate error.
        """
        command = Command()

        with self.assertRaises(CommandError) as cm:
            command.execute(
                self.public, self.private, stdout=StringIO(), update=False)

        self.assertEqual(
            "must provide a public keyfile, private keyfile and label",
            str(cm.exception))
        self.assertEqual(0, SshKeyPair.objects.count())
