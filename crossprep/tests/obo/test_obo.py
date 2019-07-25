'''Tests for building crossmap datasets from obo
'''


import unittest
from os.path import join
from crossprep.obo.build import build_obo_dataset
from crossprep.obo.obo import Obo


data_dir = join("tests", "testdata")
int_file = join(data_dir, "integers.obo")


class BuildOboDatasetTests(unittest.TestCase):
    """Configuring pubmed baseline downloads."""

    obo = Obo(int_file)

    def test_build_all(self):
        """create a dataset using entire ontology"""

        num_ids = len(self.obo.ids())
        result = build_obo_dataset(int_file)
        self.assertEqual(len(result), num_ids)

    def test_build_data_fields(self):
        """elements in dataset have primary data fields"""

        result = build_obo_dataset(int_file)
        self.assertTrue("unity" in result["int:1"]["data"])
        self.assertTrue("one" in result["int:1"]["data"])

    def test_aux_pos_fields(self):
        """elements in dataset have auxiliary data fields"""

        result = build_obo_dataset(int_file)
        self.assertTrue("integer" in result["int:1"]["aux_pos"])
        self.assertFalse("zero" in result["int:4"]["data"])
        self.assertTrue("zero" in result["int:4"]["aux_pos"])

    def test_aux_neg_fields(self):
        """elements in dataset have blanks for negative auxiliary data fields"""

        result = build_obo_dataset(int_file)
        self.assertEqual(result["int:1"]["aux_neg"], "")
        self.assertEqual(result["int:4"]["aux_neg"], "")

    def test_build_subset(self):
        """create a dataset using a branch of the ontology"""

        num_ids = len(self.obo.ids())
        result = build_obo_dataset(int_file, "int:2")
        self.assertLess(len(result), num_ids)
        self.assertTrue("int:2" in result)
