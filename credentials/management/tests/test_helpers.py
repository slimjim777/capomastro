from __future__ import unicode_literals

from tempfile import mkstemp
import os
from cStringIO import StringIO

from django.core.management.base import CommandError
from django.test import TestCase

from credentials.management.helpers import import_sshkeypair
from credentials.models import SshKeyPair


class ImportSshKeyPairTest(TestCase):

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

    def test_import_sshkeypair(self):
        """
        We can import a new keypair with a name.
        """
        stdout = StringIO()
        import_sshkeypair(
            "my test key", self.public, self.private, stdout=stdout)

        keypair = SshKeyPair.objects.get(label="my test key")
        self.assertEqual("public key", keypair.public_key)
        self.assertEqual("private key", keypair.private_key)
        self.assertEqual("Key pair created\n", stdout.getvalue())

    def test_import_sshkeypair_fails_with_preexisting_label(self):
        """
        import_sshkeypair should fail if we have a keypair with the label.
        """
        SshKeyPair.objects.create(
            label="my test", public_key="test", private_key="test")
        with self.assertRaises(CommandError) as cm:
            import_sshkeypair("my test", self.public, self.private)

        self.assertEqual("Key pair already exists", str(cm.exception))
        keypair = SshKeyPair.objects.get(label="my test")
        self.assertEqual("test", keypair.public_key)
        self.assertEqual("test", keypair.private_key)

    def test_import_sshkeypair_updates_existing_keypair(self):
        """
        import_sshkeypair should update the content if we provide a true value
        for the update parameter.
        """
        stdout = StringIO()
        SshKeyPair.objects.create(
            label="my test", public_key="test", private_key="test")
        import_sshkeypair(
            "my test", self.public, self.private, update=True, stdout=stdout)

        keypair = SshKeyPair.objects.get(label="my test")
        self.assertEqual("public key", keypair.public_key)
        self.assertEqual("private key", keypair.private_key)
        self.assertEqual("Key pair updated\n", stdout.getvalue())
