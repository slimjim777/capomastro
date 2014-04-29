from archives.models import Archive


def get_default_archive():
    """
    Find the archive that's flagged as the default.
    """
    try:
        return Archive.objects.get(default=True)
    except Archive.DoesNotExist:
        return
