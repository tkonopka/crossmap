"""
Tests for simple nearest-neighbor search
"""

import unittest
from json import dumps
from os.path import join
from crossmap.crossmap import Crossmap
from crossmap.tools import yaml_document
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
config_single = join(data_dir, "config-single.yaml")
dataset_file = join(data_dir, "dataset.yaml")
aux_file = join(data_dir, "documents.yaml")


class CrossmapSearchTests(unittest.TestCase):
    """Mapping new objects onto targets"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        # load all the target and auxiliary items
        docs, auxs = dict(), dict()
        with open(dataset_file, "rt") as f:
            for id, doc in yaml_document(f):
                docs[id] = doc
        with open(aux_file, "rt") as f:
            for id, doc in yaml_document(f):
                auxs[id] = doc
        cls.docs, cls.auxs = docs, auxs

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_output_is_serializable(self):
        """search output should be compatible with json"""

        A = self.docs["A"]
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

        A = self.docs["A"]
        result = self.crossmap.search(A, "targets", n=3)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 3)
        self.assertEqual(len(result["distances"]), 3)
        self.assertEqual(result["targets"][0], "A")

    def test_search_targets_B(self):
        """target documents should map onto themselves"""

        B = self.docs["B"]
        result = self.crossmap.search(B, "targets", n=1)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 1)
        self.assertEqual(len(result["distances"]), 1)
        self.assertEqual(result["targets"][0], "B")

    def test_search_misc_doc(self):
        """similar to dataset:documents should map to dataset:targets"""

        doc = {"data": "Catherine C",
               "aux_pos": "Alice alpha A",
               "aux_neg": "B"}
        result = self.crossmap.search(doc, "targets", n=2)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 2)
        self.assertEqual(result["targets"][0], "C")
        self.assertEqual(result["targets"][1], "A")

    def test_search_from_docs(self):
        """can map onto the documents dataset instead of dataset:targets"""

        doc = {"data": "Bob B Alice A"}
        result = self.crossmap.search(doc, "documents", n=2)
        # targets should match this document to C and A
        self.assertEqual(len(result["targets"]), 2)
        self.assertEqual(set(result["targets"]), set(["U:A", "U:B"]))


class CrossmapSearchNoDocsTests(unittest.TestCase):
    """Mapping new objects onto targets without documents"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_single)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        # load all the target and auxiliary items
        docs = dict()
        with open(dataset_file, "rt") as f:
            for id, doc in yaml_document(f):
                docs[id] = doc
        cls.docs = docs

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_single")

    def test_search_gives_output(self):
        """search should produce some output"""
        A = self.docs["A"]
        result = self.crossmap.search(A, "targets", n=3)
        result_str = dumps(result)
        self.assertTrue("A" in result_str)


class CrossmapSearchBatchTests(unittest.TestCase):
    """Mapping new objects onto targets - in batch"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        targets = dict()
        with open(dataset_file, "rt") as f:
            for id, doc in yaml_document(f):
                targets[id] = doc
        cls.targets = targets

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_file_targets(self):
        """target documents should map onto themselves"""

        target_file = self.crossmap.settings.data_files["targets"]
        result = self.crossmap.search_file(target_file, "targets", 2)
        # all items should match the raw data and map onto themselves
        self.assertEqual(len(result), len(self.targets))
        for i in range(len(result)):
            self.assertTrue(result[i]["query"] in self.targets)
            self.assertTrue(result[i]["targets"][0], result[i]["query"])

    def test_file_documents(self):
        """documents should map onto targets"""

        docs_file = self.crossmap.settings.data_files["documents"]
        result = self.crossmap.search_file(docs_file, "targets", 2)
        for i in range(len(result)):
            self.assertTrue(result[i]["targets"][0] in self.targets)
            self.assertTrue(result[i]["targets"][1] in self.targets)
