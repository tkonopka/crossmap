'''Tests for building crossmap datasets from obo

@author: Tomasz Konopka
'''


import unittest
from os.path import join
from crossprep.prep_obo import build_dataset
from crossprep.obo.obo import Obo


data_dir = join("tests", "testdata")
int_file = join(data_dir, "integers.obo")


class BuildOboDatasetTests(unittest.TestCase):
    """Configuring pubmed baseline downloads."""

    obo = Obo(int_file)

    def test_build_all(self):
        """create a dataset using entire ontology"""

        num_ids = len(self.obo.ids())
        result = build_dataset(int_file)
        self.assertEqual(len(result), num_ids)

    def test_build_subset(self):
        """create a dataset using a branch of the ontology"""

        num_ids = len(self.obo.ids())
        result = build_dataset(int_file, "int:2")
        self.assertLess(len(result), num_ids)
        self.assertTrue("int:2" in result)
