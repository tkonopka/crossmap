'''Tests for predicting new documents
'''

import unittest
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

    def test_predict_targets_A(self):
        """target documents should map onto themselves"""

        A = self.docs["A"]
        result, distances = self.crossmap.predict(A, n=3)
        self.assertEqual(len(result), 3)
        self.assertEqual(len(distances), 3)
        self.assertEqual(result[0], "A")

    def test_predict_targets_B(self):
        """target documents should map onto themselves"""

        doc = self.docs["B"]
        result, distances = self.crossmap.predict(doc, n=1)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(distances), 1)
        self.assertEqual(result[0], "B")

    def test_predict_misc_doc(self):
        """auxiliary documents should map onto dataset targets"""

        doc = {"data": "Catherine C", "aux_pos": "Alice"}
        result, _ = self.crossmap.predict(doc, n=2)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], "C")
        self.assertEqual(result[1], "A")

