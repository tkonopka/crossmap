"""
Tests for building crossmap datasets from obo
"""


import io
import unittest
import yaml
from os.path import join
from crossprep.obo.build import build_obo_dataset, build_obo_dataset_dict
from crossprep.obo.obo import Obo
from crossprep.obo.summarize import summarize_obo


data_dir = join("crossprep", "tests", "testdata")
int_file = join(data_dir, "integers.obo")


class BuildOboDatasetTests(unittest.TestCase):
    """Test functions for transferign data from obo files."""

    @classmethod
    def setUp(cls):
        cls.obo = Obo(int_file)
        raw_stream = io.StringIO()
        build_obo_dataset(int_file, out=raw_stream)
        raw_str = raw_stream.getvalue()
        raw_stream.close()
        cls.dataset = yaml.load(raw_str, Loader=yaml.CBaseLoader)

    def test_build_all(self):
        """create a dataset using entire ontology"""

        num_ids = len(self.obo.ids())
        self.assertEqual(len(self.dataset), num_ids)

    def test_build_data_fields(self):
        """elements in dataset have primary data fields"""

        result = self.dataset
        self.assertTrue("unity" in str(result["int:1"]["data_pos"]))
        self.assertTrue("one" in str(result["int:1"]["data_pos"]))

    def test_build_titles(self):
        """item have titles consisting of term names"""

        result = self.dataset
        self.assertEqual(result["int:1"]["title"], "one")
        self.assertEqual(result["int:2"]["title"], "positive integer")

    def test_aux_comment_only(self):
        """elements can have auxiliary data fields from comments"""

        result = build_obo_dataset_dict(int_file, aux="comments")
        self.assertTrue("comment" in str(result["int:0"]["data_pos"]))

    def test_aux_top(self):
        """elements can have name of top-level term"""

        plain = build_obo_dataset_dict(int_file, root_id="int:0")
        self.assertFalse("negative" in str(plain["int:6"]["data_pos"]))
        result = build_obo_dataset_dict(int_file, root_id="int:0", aux="top")
        self.assertTrue("negative" in str(result["int:6"]["data_pos"]))

    def test_aux_parents_only(self):
        """elements can have positive auxiliary data fields from parents"""

        result = build_obo_dataset_dict(int_file, aux="parents")
        self.assertTrue("integer" in str(result["int:1"]["data_pos"]))
        self.assertFalse("comment" in str(result["int:1"]["data_pos"]))
        r4 = result["int:4"]
        self.assertTrue("zero" in str(r4["data_pos"]))

    def test_aux_parents_comments(self):
        """elements can have auxiliary fields from comments of parents"""

        result = build_obo_dataset_dict(int_file, aux="parents,comments")
        self.assertTrue("integer" in str(result["int:1"]["data_pos"]))
        self.assertTrue("comment" in str(result["int:1"]["data_pos"]))

    def test_aux_siblings(self):
        """elements can have negative auxiliary data fields from siblings"""

        result = build_obo_dataset_dict(int_file, aux="siblings")
        r4 = result["int:4"]
        self.assertTrue("prime" in str(r4["data_neg"]))

    def test_aux_children(self):
        """elements can have negative auxiliary data fields from children"""

        result = build_obo_dataset_dict(int_file, aux="children")
        r2 = result["int:2"]
        self.assertTrue("prime" in str(r2["data_neg"]))

    def test_aux_both_intermediate(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset_dict(int_file, aux="parents,children,siblings")
        # int:4 is a node with both parent and siblings
        r4 = result["int:4"]
        self.assertTrue("prime" in str(r4["data_neg"]))
        self.assertTrue("greater" in str(r4["data_pos"]))

    def test_aux_both_nosib(self):
        """elements can have both positive and negative aux fields"""

        result = build_obo_dataset_dict(int_file, aux="parents,children,siblings")
        # check that some negative data are provided in the result
        r4 = result["int:4"]
        self.assertTrue("prime" in str(r4["data_neg"]))
        # although negative aux are allowed, the r6 node does not have any siblings
        r6 = result["int:6"]
        self.assertTrue("less" in str(r6["data_pos"]))

    def test_aux_synonyms(self):
        """elements can include synonyms"""

        result = build_obo_dataset_dict(int_file, aux="parents,synonyms")
        self.assertTrue("unity" in str(result["int:6"]["data_pos"]))
        self.assertFalse("EXACT" in str(result["int:6"]))

    def test_build_subset(self):
        """create a dataset using a branch of the ontology"""

        num_ids = len(self.obo.ids())
        result = build_obo_dataset_dict(int_file, "int:2")
        self.assertLess(len(result), num_ids)
        self.assertTrue("int:2" in result)

    def test_aux_ancestors(self):
        """elements can have all ancestors listed"""

        result = build_obo_dataset_dict(int_file, aux="ancestors")
        self.assertTrue("integer" in str(result["int:5"]["data_pos"]))
        self.assertTrue("root" in str(result["int:5"]["data_pos"]))


class SummarizeOboTests(unittest.TestCase):
    """Counting fields in obo files"""

    @classmethod
    def setUp(cls):
        cls.obo = Obo(int_file)
        cls.summary = summarize_obo(int_file)

    def test_length(self):
        """summary should be a list with one items per obo id"""

        self.assertTrue(type(self.summary) is list)
        self.assertEqual(len(self.summary), 7)
