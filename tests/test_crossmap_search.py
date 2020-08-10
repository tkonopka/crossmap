"""
Tests for simple nearest-neighbor search
"""

import unittest
from json import dumps
from os.path import join
from crossmap.crossmap import Crossmap
from crossmap.tools import read_yaml_documents
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
config_single = join(data_dir, "config-single.yaml")
dataset_file = join(data_dir, "dataset.yaml")
aux_file = join(data_dir, "documents.yaml")
bad_file = join(data_dir, "bad_data_fields.yaml")

# read the docs from the dataset
dataset_docs = read_yaml_documents(dataset_file)
aux_docs = read_yaml_documents(aux_file)


class CrossmapSearchTests(unittest.TestCase):
    """Mapping new objects onto targets"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_output_is_serializable(self):
        """search output should be compatible with json"""

        A = dataset_docs["A"]
        result = self.crossmap.search(A, "targets", n=3)
        result_str = dumps(result)
        self.assertTrue("A" in result_str)

    def test_search_empty(self):
        """search given an empty document should not raise exceptions"""

        empty = dict(data="")
        result = self.crossmap.search(empty, "targets", n=3)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 0)
        self.assertEqual(len(result["distances"]), 0)

    def test_search_targets_A(self):
        """target documents should map onto themselves"""

        A = dataset_docs["A"]
        result = self.crossmap.search(A, "targets", n=3)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 3)
        self.assertEqual(len(result["distances"]), 3)
        self.assertEqual(result["targets"][0], "A")

    def test_search_targets_B(self):
        """target documents should map onto themselves"""

        B = dataset_docs["B"]
        result = self.crossmap.search(B, "targets", n=1)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 1)
        self.assertEqual(len(result["distances"]), 1)
        self.assertEqual(result["targets"][0], "B")

    def test_search_misc_doc(self):
        """similar to dataset:documents should map to dataset:targets"""

        # document overlapping with C and A, with a slight bias toward C
        doc = {"data_pos": "Catherine C C. Alice alpha A",
               "data_neg": "B"}
        result = self.crossmap.search(doc, "targets", n=2)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 2)
        self.assertEqual(result["targets"][0], "C")
        self.assertEqual(result["targets"][1], "A")

    def test_search_from_docs(self):
        """can map onto the documents dataset instead of dataset:targets"""

        doc = {"data_pos": "Bob B Alice A"}
        result = self.crossmap.search(doc, "documents", n=2)
        # targets should match this document to C and A
        self.assertEqual(len(result["targets"]), 2)
        self.assertEqual(set(result["targets"]), set(["U:A", "U:B"]))

    def test_search_from_only_negative(self):
        """search can accept only-negative values"""

        doc = {"values": {"A": -1, "B": -1}}
        result = self.crossmap.search(doc, "documents", n=2)
        # targets should avoid database targets with A and B
        self.assertFalse("U:A" in set(result["targets"]))
        self.assertFalse("U:B" in set(result["targets"]))


class CrossmapSearchSingleTests(unittest.TestCase):
    """Mapping new objects onto targets, config with a single collection"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_single)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_single")

    def test_search_gives_output(self):
        """search should produce some output"""
        A = dataset_docs["A"]
        result = self.crossmap.search(A, "targets", n=3)
        result_str = dumps(result)
        self.assertTrue("A" in result_str)

    def test_search_avoids_no_match_outputs(self):
        """search should avoid reporting items that are distance=1"""

        doc = dict(data="Daniel")
        # doc has a feature that is present in just one data item
        result = self.crossmap.search(doc, "targets", n=4)
        # so output should contain only one hit, even if n>1
        self.assertEqual(len(result["targets"]), 1)

    def test_search_can_report_no_match_outputs(self):
        """search should avoid reporting items that are distance=1"""

        doc = dict(data="Daniel")
        # doc has a feature that is present in just one data item
        # non-default behavior can report up to n hits
        self.crossmap.indexer.trim_search = 0
        result = self.crossmap.search(doc, "targets", n=4)
        self.assertEqual(len(result["targets"]), 4)

class CrossmapSearchBatchTests(unittest.TestCase):
    """Mapping new objects onto targets - in batch"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_file_targets(self):
        """target documents should map onto themselves"""

        crossmap = self.crossmap
        target_file = crossmap.settings.data.collections["targets"]
        result = crossmap.search_file(target_file, "targets", 2)
        # all items should match the raw data and map onto themselves
        self.assertEqual(len(result), len(dataset_docs))
        for i in range(len(result)):
            self.assertTrue(result[i]["query"] in dataset_docs)
            self.assertTrue(result[i]["targets"][0], result[i]["query"])

    def test_file_documents(self):
        """documents should map onto targets"""

        crossmap = self.crossmap
        docs_file = crossmap.settings.data.collections["documents"]
        result = crossmap.search_file(docs_file, "targets", 2)
        for i in range(len(result)):
            if len(result[i]["targets"]) > 0:
                self.assertTrue(result[i]["targets"][0] in dataset_docs)
            if len(result[i]["targets"]) > 1:
                self.assertTrue(result[i]["targets"][1] in dataset_docs)

    def test_complains_improper_filed(self):
        """should raise if data file has improper content"""

        with self.assertLogs(level="ERROR") as cm:
            self.crossmap.search_file(bad_file, "targets", 2)
        self.assertTrue("title" in str(cm.output))

