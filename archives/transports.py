import os
import urllib2
import logging
import base64
import subprocess

from paramiko import SSHClient, WarningPolicy

from archives.sftpclient import SFTPClient


class Transport(object):
    """
    Responsible for reading the artifacts from
    jenkins and writing them to the target archive.
    """
    checksum_filename = "SHA256SUMS"

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
        self._run_command("cd `dirname %s` && sha256sum %s >> %s" % (
            self.get_relative_filename(archived_artifact.archived_path),
            archived_artifact.artifact.filename,
            self.checksum_filename))

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
        logging.info("Attempting to archive %s to %s", url, destination_path)
        request = urllib2.Request(url)
        request.add_header(
            "Authorization",
            "Basic " + base64.b64encode(username + ":" + password))
        f = urllib2.urlopen(request)
        return self.archive_file(f, destination_path)

    def _run_command(self, command):
        """
        Runs a command on the archive.
        """
        raise NotImplemented

    def link_filename_to_filename(self, source, destination):
        """
        Link a filename to another filename in the transport's backend.
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

        Returns the number of bytes archived.
        """
        filename = self.get_relative_filename(filename)
        if not os.path.exists(os.path.dirname(filename)):
            os.makedirs(os.path.dirname(filename))
        logging.info(
            "LocalTransport archiving artifact to %s", filename)

        # We use the low-level stuff here because Python2 returns None from
        # fileobj.write()
        try:
            fd = os.open(filename, os.O_RDWR | os.O_CREAT)
            size = os.write(fd, fileobj.read())
        finally:
            os.close(fd)
        return size

    def _run_command(self, command):
        """
        Runs a command in a local shell.
        """
        # TODO: raise exception if the command fails
        logging.debug("Executing %s" % command)
        subprocess.Popen(command, stdout=subprocess.PIPE, shell=True).stdout.read()

    def archive_url(self, url, destination_path, username, password):
        """
        Archives a single fileobj to the destination path.
        """
        logging.info("Attempting to archive %s to %s", url, destination_path)
        request = urllib2.Request(url)
        request.add_header(
            "Authorization",
            "Basic " + base64.b64encode(username + ":" + password))
        f = urllib2.urlopen(request)
        return self.archive_file(f, destination_path)

    def link_filename_to_filename(self, source, destination):
        """
        Hard link a file in the filesystem, only if the file doesn't already
        exist.
        """
        source = self.get_relative_filename(source)
        destination = self.get_relative_filename(destination)

        if not os.path.exists(os.path.dirname(destination)):
            os.makedirs(os.path.dirname(destination))
        if not os.path.exists(destination):
            os.link(source, destination)


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
            username=self.archive.username,
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
        destination = self.get_relative_filename(filename)
        self._run_command("mkdir -p `dirname %s`" % destination)
        # TODO: raise exception if the command fails
        logging.info(
            "SshTransport archiving artifact to %s", filename)
        return self.sftp_client.stream_file_to_remote(fileobj, destination)

    def link_filename_to_filename(self, source, destination):
        """
        Hard link a file in the filesystem.
        """
        source = self.get_relative_filename(source)
        destination = self.get_relative_filename(destination)

        # TODO: Use the return value from the call to work out if we were
        # successful or not.
        self._run_command("mkdir -p `dirname %s`" % destination)
        self._run_command("ln \"%s\" \"%s\"" % (source, destination))
