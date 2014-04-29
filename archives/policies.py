from django.utils.text import slugify


class DefaultPolicy(object):
    """
    Base ArchivePolicy class. Calculates a basic path based on the basedir and
    filename.
    """
    def get_path_for_artifact(self, artifact, **kwargs):
        """
        Returns a filesystem path for an artifact.
        """
        return artifact.filename


class CdimageArchivePolicy(object):
    """
    Converts jenkins artifact urls to a cdimage-like structure.
    """
    def get_path_for_artifact(self, artifact, projectbuild):
        """
        Returns a cdimage-like relative path.
        """
        return "{project}/{build_id}/{filename}".format(
            **{
                "project": slugify(projectbuild.project.name),
                "build_id": projectbuild.build_id,
                "filename": artifact.filename
            })
