"""
Tests for building crossmap datasets from opentargets json-like data
"""


import unittest
from os.path import join
from crossprep.opentargets.build import build_opentargets_dataset


data_dir = join("crossprep", "tests", "testdata")
# opentargets calls their files "json" but actually they
# are a one-line-per-item format.
# each line is a valid json object, but the lines are all independent
associations_file = join(data_dir, "opentargets.json")

id1 = "OT:ENSG00000121879-MONDO_0045024"


class BuildOpentargetsDatasetTests(unittest.TestCase):
    """creating a dataset from json-like opentargets data."""

    @classmethod
    def setUp(cls):
        cls.dataset = build_opentargets_dataset(associations_file)
        cls.data1 = cls.dataset[id1]["data"]

    def test_length(self):
        """dataset has three disorders"""

        self.assertEqual(len(self.dataset), 3)

    def test_data_components(self):

        self.assertTrue("tractability" in self.data1)
        self.assertTrue("gene" in self.data1)
        self.assertTrue("disease" in self.data1)

    def test_gene(self):
        """item has gene information"""

        self.assertTrue("PIK3CA" in str(self.data1))

    def test_disease(self):
        """item has disease information"""

        self.assertTrue("neoplastic" in str(self.data1))

    def test_tractability(self):
        """item has disease information"""

        self.assertTrue("antibody" in str(self.data1))
        self.assertTrue("molecule" in str(self.data1))

