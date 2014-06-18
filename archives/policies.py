import time

from django.utils.text import slugify


class DefaultPolicy(object):
    """
    Base ArchivePolicy class. Calculates a basic path based on the basedir and
    filename.
    """
    def get_path_for_artifact(
            self, artifact, build=None, dependency=None, projectbuild=None):
        """
        Returns a filesystem path for an artifact.
        """
        build_id = "%s-%s" % (
            build.created_at.strftime("%Y-%m-%d"),
            time.mktime(build.created_at.timetuple()))
        return "{dependency}/{build_id}/{filename}".format(
            dependency=slugify(dependency.name),
            build_id=build_id,
            filename=artifact.filename)


class CdimageArchivePolicy(DefaultPolicy):
    """
    Converts jenkins artifact urls to a cdimage-like structure.
    """
    def get_path_for_artifact(
            self, artifact, build=None, dependency=None, projectbuild=None):
        """
        Returns a cdimage-like relative path.
        """
        if projectbuild:
            return "{project}/{build_id}/{filename}".format(
                project=slugify(projectbuild.project.name),
                build_id=projectbuild.build_id,
                filename=artifact.filename)
        else:
            return super(CdimageArchivePolicy, self).get_path_for_artifact(
                artifact, build=build, dependency=dependency,
                projectbuild=projectbuild)
