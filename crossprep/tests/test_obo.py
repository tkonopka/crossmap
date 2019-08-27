'''Tests for building crossmap datasets from obo
'''


import unittest
from os.path import join
from crossprep.obo.build import build_obo_dataset
from crossprep.obo.obo import Obo


data_dir = join("crossprep", "tests", "testdata")
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

    def test_aux_P_only(self):
        """elements can have positive auxiliary data fields"""

        result = build_obo_dataset(int_file, aux_pos=True, aux_neg=False)
        self.assertTrue("integer" in result["int:1"]["aux_pos"])
        # r4
        r4 = result["int:4"]
        self.assertFalse("zero" in r4["data"])
        self.assertTrue("zero" in r4["aux_pos"])
        self.assertEqual(r4["aux_neg"], "")

    def test_aux_N_siblings(self):
        """elements can have negative auxiliary data fields from siblings"""

        result = build_obo_dataset(int_file, aux_pos=False, aux_neg=True)
        r4 = result["int:4"]
        self.assertEqual(r4["aux_pos"], "")
        self.assertTrue("prime" in r4["aux_neg"])

    def test_aux_N_children(self):
        """elements can have negative auxiliary data fields from siblings"""

        result = build_obo_dataset(int_file, aux_pos=False, aux_neg=True)
        r2 = result["int:2"]
        self.assertEqual(r2["aux_pos"], "")
        self.assertTrue("prime" in r2["aux_neg"])

    def test_aux_both_intermediate(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset(int_file, aux_pos=True, aux_neg=True)
        # int:4 is a node with both parent and siblings
        r4 = result["int:4"]
        self.assertTrue("prime" in r4["aux_neg"])
        self.assertTrue("greater" in r4["aux_pos"])

    def test_aux_both_nosib(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset(int_file, aux_pos=True, aux_neg=True)
        # check that some negative data are provided in the result
        r4 = result["int:4"]
        self.assertTrue("prime" in r4["aux_neg"])
        # although negative aux are allowed, the r6 node does not have any siblings
        r6 = result["int:6"]
        self.assertEqual(r6["aux_neg"], "")
        self.assertTrue("less" in r6["aux_pos"])

    def test_build_subset(self):
        """create a dataset using a branch of the ontology"""

        num_ids = len(self.obo.ids())
        result = build_obo_dataset(int_file, "int:2")
        self.assertLess(len(result), num_ids)
        self.assertTrue("int:2" in result)

    def test_build_subset(self):
        """create a dataset using a branch of the ontology"""

        num_ids = len(self.obo.ids())
        result = build_obo_dataset(int_file, "int:2")
        self.assertLess(len(result), num_ids)
        self.assertTrue("int:2" in result)
