'''Tests for predicting new documents
'''

import unittest
from json import dumps
from os.path import join
from crossmap.crossmap import Crossmap
from crossmap.tools import yaml_document
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
dataset_file = join(data_dir, "dataset.yaml")
aux_file = join(data_dir, "documents.yaml")


class CrossmapPredictTests(unittest.TestCase):
    """Mapping new objects onto targets"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        # load all the target and auxiliary items
        cls.docs = dict()
        cls.auxs = dict()
        with open(dataset_file, "rt") as f:
            for id, doc in yaml_document(f):
                cls.docs[id] = doc
        with open(aux_file, "rt") as f:
            for id, doc in yaml_document(f):
                cls.auxs[id] = doc

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_prediction_is_serializable(self):
        """prediction output should be compatible with json"""
        A = self.docs["A"]
        result = self.crossmap.predict(A, n=3)
        result_str = dumps(result)
        self.assertTrue("A" in result_str)

    def test_predict_targets_A(self):
        """target documents should map onto themselves"""

        A = self.docs["A"]
        result = self.crossmap.predict(A, n=3)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 3)
        self.assertEqual(len(result["distances"]), 3)
        self.assertEqual(result["targets"][0], "A")

    def test_predict_targets_B(self):
        """target documents should map onto themselves"""

        doc = self.docs["B"]
        result = self.crossmap.predict(doc, n=1)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 1)
        self.assertEqual(len(result["distances"]), 1)
        self.assertEqual(result["targets"][0], "B")

    def test_predict_misc_doc(self):
        """auxiliary documents should map onto dataset targets"""

        doc = {"data": "Catherine C",
               "aux_pos": "Alice alpha A",
               "aux_neg": "B"}
        result = self.crossmap.predict(doc, n=2)
        self.assertTrue(type(result) is dict)
        self.assertEqual(len(result["targets"]), 2)
        self.assertEqual(result["targets"][0], "C")
        self.assertEqual(result["targets"][1], "A")


class CrossmapPredictBatchTests(unittest.TestCase):
    """Mapping new objects onto targets - in batch"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        cls.targets = dict()
        with open(dataset_file, "rt") as f:
            for id, doc in yaml_document(f):
                cls.targets[id] = doc

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_file_targets(self):
        """target documents should map onto themselves"""

        target_file = self.crossmap.settings.files("targets")[0]
        result = self.crossmap.predict_file(target_file, 2)
        # all items should match the raw data and map onto themselves
        self.assertEqual(len(result), len(self.targets))
        for i in range(len(result)):
            self.assertTrue(result[i]["query"] in self.targets)
            self.assertTrue(result[i]["targets"][0], result[i]["query"])

    def test_file_documents(self):
        """documents should map onto targets"""

        docs_file = self.crossmap.settings.files("documents")[0]
        result = self.crossmap.predict_file(docs_file, 2)
        for i in range(len(result)):
            self.assertTrue(result[i]["targets"][0] in self.targets)
            self.assertTrue(result[i]["targets"][1] in self.targets)
