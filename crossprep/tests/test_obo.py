"""
Tests for building crossmap datasets from obo
"""


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

    def test_build_titles(self):
        """item have titles consisting of term names"""

        result = build_obo_dataset(int_file)
        self.assertEqual(result["int:1"]["title"], "one")
        self.assertEqual(result["int:2"]["title"], "positive integer")

    def test_aux_comment_only(self):
        """elements can have auxiliary data fields from comments"""

        result = build_obo_dataset(int_file, aux="comments")
        self.assertTrue("comment" in result["int:0"]["aux_pos"])
        self.assertEqual(result["int:1"]["aux_pos"], "")

    def test_aux_parents_only(self):
        """elements can have positive auxiliary data fields from parents"""

        result = build_obo_dataset(int_file, aux="parents")
        self.assertTrue("integer" in result["int:1"]["aux_pos"])
        self.assertFalse("comment" in result["int:1"]["aux_pos"])
        r4 = result["int:4"]
        self.assertFalse("zero" in r4["data"])
        self.assertTrue("zero" in r4["aux_pos"])
        self.assertEqual(r4["aux_neg"], "")

    def test_aux_parents_comments(self):
        """elements can have auxiliary fields from comments of parents"""

        result = build_obo_dataset(int_file, aux="parents,comments")
        self.assertTrue("integer" in result["int:1"]["aux_pos"])
        self.assertTrue("comment" in result["int:1"]["aux_pos"])

    def test_aux_siblings(self):
        """elements can have negative auxiliary data fields from siblings"""

        result = build_obo_dataset(int_file, aux="siblings")
        r4 = result["int:4"]
        self.assertEqual(r4["aux_pos"], "")
        self.assertTrue("prime" in r4["aux_neg"])

    def test_aux_children(self):
        """elements can have negative auxiliary data fields from siblings"""

        result = build_obo_dataset(int_file, aux="children")
        r2 = result["int:2"]
        self.assertEqual(r2["aux_pos"], "")
        self.assertTrue("prime" in r2["aux_neg"])

    def test_aux_both_intermediate(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset(int_file, aux="parents,children,siblings")
        # int:4 is a node with both parent and siblings
        r4 = result["int:4"]
        self.assertTrue("prime" in r4["aux_neg"])
        self.assertTrue("greater" in r4["aux_pos"])

    def test_aux_both_nosib(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset(int_file, aux="parents,children,siblings")
        # check that some negative data are provided in the result
        r4 = result["int:4"]
        self.assertTrue("prime" in r4["aux_neg"])
        # although negative aux are allowed, the r6 node does not have any siblings
        r6 = result["int:6"]
        self.assertEqual(r6["aux_neg"], "")
        self.assertTrue("less" in r6["aux_pos"])

    def test_aux_synonyms(self):
        """elements can include synonyms"""

        result = build_obo_dataset(int_file, aux="parents,synonyms")
        self.assertTrue("unity" in result["int:6"]["aux_pos"])
        self.assertFalse("EXACT" in str(result["int:6"]))

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

    def test_aux_ancestors(self):
        """elements can have all ancestors listed"""

        result = build_obo_dataset(int_file, aux="ancestors")
        self.assertTrue("integer" in result["int:5"]["aux_pos"])
        self.assertTrue("root" in result["int:5"]["aux_pos"])
