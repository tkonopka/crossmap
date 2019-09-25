"""
Tests for computing specific distances (for debugging/inspection purposes)
"""

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.settings import CrossmapSettings
from crossmap.tools import read_dict
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_simple = join(data_dir, "config-simple.yaml")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapDistanceTests(unittest.TestCase):
    """Use crossmap interface to compute distance betwee data objects
    and items in db"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_simple)
        cls.crossmap = Crossmap(settings)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_distance_to_targets(self):
        """extract individual distance values"""

        doc = {"data": "Bob B Alice A B"}
        result = self.crossmap.distance(doc, ids=["A", "C"])
        self.assertEqual(len(result), 2)
        self.assertTrue("target" in result[0] and "document" not in result[0])
        self.assertTrue("target" in result[1] and "document" not in result[1])
        # outputs are in same order as ids in array
        self.assertEqual(result[0]["target"], "A")
        self.assertEqual(result[1]["target"], "C")

    def test_distance_to_documents(self):
        """extract individual distance values"""

        doc = {"data": "Bob B Alice A B"}
        result = self.crossmap.distance(doc, ids=["U:B", "U:E"])
        self.assertEqual(len(result), 2)
        self.assertTrue("target" not in result[0] and "document" in result[0])
        self.assertTrue("target" not in result[1] and "document" in result[1])
        # outputs are in same order as ids in array
        self.assertEqual(result[0]["document"], "U:B")
        self.assertEqual(result[1]["document"], "U:E")

    def test_distance_to_mix_targets_documents(self):
        """extract individual distance values to targets and documents at once"""

        doc = {"data": "Bob B Alice A B"}
        result = self.crossmap.distance(doc, ids=["C", "U:E"])
        self.assertEqual(len(result), 2)
        self.assertTrue("target" in result[0] and "document" not in result[0])
        self.assertTrue("target" not in result[1] and "document" in result[1])
        # outputs are in same order as ids in array
        self.assertEqual(result[0]["target"], "C")
        self.assertEqual(result[1]["document"], "U:E")
