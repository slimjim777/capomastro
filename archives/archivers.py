import os
import urllib2

from paramiko import SSHClient, WarningPolicy
from paramiko import SFTPClient as BaseSFTPClient


class Archiver(object):
    """
    Responsible for reading the artifacts from
    jenkins and writing them to the target archive.
    """
    def __init__(self, policy, target):
        self.policy = policy
        self.target = target

    def start(self):
        """
        Initialize the archiving.
        """

    def end(self):
        """
        Finalize the archiving.
        """

    def archive_artifact(self, artifact_url, destination_path):
        """
        Archives a single artifact from the url to the
        destination path.
        """
        raise NotImplemented

    def archive(self):
        """
        Archives all mapped artifacts from the policy to the
        target archive.
        """
        mappings = self.policy.get_mappings()
        self.start()
        for artifact_url in mappings.keys():
            self.archive_artifact(artifact_url, mappings[artifact_url])
        self.end()


class SFTPClient(BaseSFTPClient):
    def stream_file_to_remote(self, fileobj, remotepath):
        """
        Reads from fileobj and streams it to a remote server over ssh.
        """
        try:
            fr = self.file(remotepath, "wb")
            fr.set_pipelined(True)
            size = 0
            try:
                while True:
                    data = fileobj.read(32768)
                    if len(data) == 0:
                        break
                    fr.write(data)
                    size += len(data)
            finally:
                fr.close()
        finally:
            fileobj.close()
        s = self.stat(remotepath)
        if s.st_size != size:
            raise IOError("size mismatch in put! %d != %d" % (s.st_size, size))
        return s


class SshArchiver(Archiver):
    """
    Archives artifacts using ssh.
    """

    def start(self):
        """
        Opens the ssh connection.
        """
        self.ssh_client = SSHClient()
        self.ssh_client.set_missing_host_key_policy(WarningPolicy())
        self.ssh_client.connect(
            self.target.host,
            username = self.target.username,
            pkey=self.target.ssh_credentials.get_pkey())
        self.sftp_client = SFTPClient.from_transport(
            self.ssh_client.get_transport())

    def end(self):
        """
        Closes the ssh connection.
        """
        self.ssh_client.close()

    def archive_artifact(self, artifact_url, destination):
        """
        Uploads the artifact_url to the destination on
        the remote server, underneath the target's basedir.
        """
        destination = os.path.join(self.target.basedir, destination)
        _, stdout, _ = self.ssh_client.exec_command(
            "mkdir -p `dirname %s`" % destination)
        # TODO: raise exception if the command fails
        _ = stdout.channel.recv_exit_status()  # noqa
        artifact = urllib2.urlopen(artifact_url)
        self.sftp_client.stream_file_to_remote(artifact, destination)
