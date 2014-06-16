import os
import urllib2
import logging
import base64
import subprocess

from paramiko import SSHClient, WarningPolicy

from archives.sftpclient import SFTPClient

logger = logging.getLogger(__name__)


class Transport(object):
    """
    Responsible for reading the artifacts from
    jenkins and writing them to the target archive.
    """
    def __init__(self, archive):
        self.archive = archive

    def start(self):
        """
        Initialize the archiving.
        """

    def end(self):
        """
        Finalize the archiving.
        """

    def archive_file(self, fileobj, destination_path):
        """
        Archives a single fileobj to the destination path.
        """
        raise NotImplemented

    def generate_checksums(self, archived_artifact):
        """
        Generates checksum files for the specified artifact on the archive.
        """
        checksum_filename = "SHA256SUMS"
        self._run_command("cd `dirname %s`; sha256sum %s >> %s" % (
            archived_artifact.archived_path,
            archived_artifact.artifact.filename,
            checksum_filename))

    def get_relative_filename(self, filename):
        """
        We strip the leading / from the destination_path to root the new files
        at base_dir.
        """
        return os.path.join(self.archive.basedir, filename.lstrip("/"))

    def archive_url(self, url, destination_path, username, password):
        """
        Archives a single fileobj to the destination path.
        """
        logger.info("Attempting to archive %s to %s", url, destination_path)
        request = urllib2.Request(url)
        request.add_header(
            "Authorization",
            "Basic " + base64.b64encode(username + ":" + password))
        f = urllib2.urlopen(request)
        self.archive_file(f, destination_path)

    def _run_command(self, command):
        """
        Runs a command on the archive.
        """
        raise NotImplemented


class LocalTransport(Transport):
    """
    Responsible for reading the artifacts from
    jenkins and writing them to the target archive.
    """
    def start(self):
        """
        Initialize the archiving.
        """
        if not os.path.exists(self.archive.basedir):
            os.makedirs(self.archive.basedir)

    def archive_file(self, fileobj, filename):
        """
        Archives a single artifact from the fileobj to the
        destination path.
        """
        filename = self.get_relative_filename(filename)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        logger.info(
            "LocalTransport archiving artifact to %s", filename)
        open(filename, "w").write(fileobj.read())
        return filename

    def _run_command(self, command):
        """
        Runs a command in a local shell.
        """
        # TODO: raise exception if the command fails
        subprocess.Popen(command, shell=True).stdout.read()


class SshTransport(Transport):
    """
    Archives artifacts using ssh.
    """

    def _get_ssh_clients(self):
        """
        Returns an SSHClient and SFTPClient configured for use.
        """
        ssh_client = SSHClient()
        ssh_client.set_missing_host_key_policy(WarningPolicy())
        ssh_client.connect(
            self.archive.host,
            username = self.archive.username,
            pkey=self.archive.ssh_credentials.get_pkey())
        sftp_client = SFTPClient.from_transport(
            ssh_client.get_transport())
        return ssh_client, sftp_client

    def _run_command(self, command):
        """
        Runs a command over the ssh connection, makes sure it finishes.
        """
        # TODO: raise exception if the command fails
        _, stdout, _ = self.ssh_client.exec_command(command)
        _ = stdout.channel.recv_exit_status()  # noqa

    def start(self):
        """
        Opens the ssh connection.
        """
        self.ssh_client, self.sftp_client = self._get_ssh_clients()

    def end(self):
        """
        Closes the ssh connection.
        """
        self.ssh_client.close()

    def archive_file(self, fileobj, filename):
        """
        Uploads the artifact_url to the destination on
        the remote server, underneath the target's basedir.
        """
        destination =  self.get_relative_filename(filename)
        self._run_command("mkdir -p `dirname %s`" % destination)
        logger.info(
            "SshTransport archiving artifact to %s", filename)
        self.sftp_client.stream_file_to_remote(fileobj, destination)

