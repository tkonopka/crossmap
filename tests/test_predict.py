'''Tests for predicting new documents
'''

import unittest
from os.path import join
from crossmap.crossmap import Crossmap
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "crossmap.yaml")
dataset_file = join(data_dir, "dataset.yaml")
aux_file = join(data_dir, "documents.yaml")

@unittest.skip
class CrossmapPredictTests(unittest.TestCase):
    """Mapping new objects onto targets"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap0")
        cls.crossmap = Crossmap(config_plain)

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_embedding_exists(self):
        """internal check: class setup build a crossmap object"""
        self.assertEqual(self.crossmap.settings.name, "crossmap0")

    def test_predict_targets(self):
        """target documents should map onto themselves"""

        tokens = self.crossmap.tokenizer.tokenize(dataset_file)
        result = self.crossmap.predict(dataset_file)
        self.assertEqual(len(result), len(tokens))
        for k,v in result.items():
            self.assertEqual(k, v, "all items should match to themselves")

    def test_predict_axiliary(self):
        """auxiliary documents should map onto dataset targets"""

        tokens = self.crossmap.tokenizer.tokenize(aux_file)
        result = self.crossmap.predict(aux_file)
        self.assertEqual(len(result), len(tokens))
        target_ids = self.crossmap.target_ids
        for k, v in result.items():
            self.assertTrue(v in target_ids, "all items should match to targets")

