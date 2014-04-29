from __future__ import unicode_literals

from django.test import TestCase

from .factories import ArchiveFactory
from archives.helpers import get_default_archive


class GetDefaultArchiveTest(TestCase):

    def test_get_default_archive(self):
        """
        Return the archive with the default flag set to True.
        """
        self.assertIsNone(get_default_archive())

        default = ArchiveFactory.create(name="default", default=True)
        self.assertEqual(default, get_default_archive())
