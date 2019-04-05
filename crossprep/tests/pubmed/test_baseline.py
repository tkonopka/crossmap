'''Tests for pubmed baseline downloads

@author: Tomasz Konopka
'''


import unittest
from crossprep.pubmed.baseline import template_format


class BaselineTests(unittest.TestCase):
    """Configuring pubmed baseline downloads."""

    def test_template_format(self):
        """Can create a database file"""

        hashes, format = template_format("pubmed19n####.xml.gz")
        self.assertEqual(hashes, "####")
        self.assertEqual(format, "{:04}")
        self.assertEqual(format.format(2), "0002")
