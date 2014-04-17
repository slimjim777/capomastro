from django.core.management.base import CommandError

from credentials.models import SshKeyPair


def import_sshkeypair(
        label, public_key, private_key, update=False, stdout=None):
    """
    Import or update content to the specified label.
    """
    with open(public_key) as public:
        with open(private_key) as private:
            try:
                existing = SshKeyPair.objects.get(label=label)
                if update:
                    existing.public_key = public.read()
                    existing.private_key = private.read()
                    existing.save()
                    if stdout:
                        stdout.write("Key pair updated\n")
                else:
                    raise CommandError("Key pair already exists")
            except SshKeyPair.DoesNotExist:
                SshKeyPair.objects.create(
                    label=label, public_key=public.read(),
                    private_key=private.read())
                if stdout:
                    stdout.write("Key pair created\n")
