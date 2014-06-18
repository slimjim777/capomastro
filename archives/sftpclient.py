from paramiko import SFTPClient as BaseSFTPClient


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
