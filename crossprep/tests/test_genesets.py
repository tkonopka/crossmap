'''Tests for building crossmap datasets from gene sets
'''


import unittest
from os.path import join
from crossprep.genesets.build import build_gmt_dataset


data_dir = join("crossprep", "tests", "testdata")
tsv_file = join(data_dir, "geneset.tsv")
gmt_file = join(data_dir, "geneset.gmt")


class BuildGenesetDatasetTests(unittest.TestCase):
    """creating a dataset from a tsv file."""

    def test_gmt_basic(self):
        """dataset has three genesets"""

        result = build_gmt_dataset(gmt_file)
        self.assertEqual(len(result), 3)
        self.assertTrue("S:01" in str(list(result.keys())))
        self.assertTrue("small" in result["S:01"]["data"])
        self.assertTrue("medium" in result["S:02"]["data"])
        self.assertTrue("A1" in result["S:02"]["aux_pos"])
        self.assertTrue("A5" in result["S:02"]["aux_pos"])

    def test_gmt_skip_small(self):
        """dataset has three genesets"""

        result = build_gmt_dataset(gmt_file, min_size=3)
        self.assertEqual(len(result), 2)
        self.assertFalse("S:01" in result)
        self.assertTrue("S:02" in result)
        self.assertTrue("S:03" in result)

    def test_gmt_skip_large(self):
        """dataset has three genesets"""

        result = build_gmt_dataset(gmt_file, min_size=0, max_size=6)
        self.assertEqual(len(result), 2)
        self.assertTrue("S:01" in result)
        self.assertTrue("S:02" in result)
        self.assertFalse("S:03" in result)