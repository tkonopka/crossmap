'''Tests for mapping across datasets using token similarities

@author: Tomasz Konopka
'''

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "crossmap.yaml")
config_exclude = join(data_dir, "crossmap-exclude.yaml")

include_file = join(data_dir, "include.txt")
exclude_file = join(data_dir, "exclude.txt")
exclude_file2 = join(data_dir, "exclude_2.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapInitTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_init_default(self):
        """Configure a crossmap with just a directory"""

        crossmap = Crossmap(data_dir)
        self.assertEqual(crossmap.settings.dir, data_dir)
        self.assertEqual(crossmap.settings.name, "crossmap0",
                         "crossmap0 is the name defined in config.yaml file")
        self.assertEqual(crossmap.settings.data_dir,
                         join(data_dir, "crossmap0"))

    def test_target_tokens(self):
        """Extract tokens from target objects"""

        crossmap = Crossmap(config_plain)
        crossmap_dir = crossmap.settings.data_dir
        # token cache should not exist
        toks_file = join(crossmap_dir, "crossmap0-target-features.tsv")
        self.assertFalse(exists(toks_file))
        # first iteration should create the cache file
        with self.assertLogs(level="INFO") as cm1:
            ids1, tokens1 = crossmap.targets_features()
        self.assertTrue("Extracting" in str(cm1.output))
        self.assertTrue(exists(toks_file))
        self.assertTrue("with" in tokens1)
        self.assertTrue("start" in tokens1)
        self.assertTrue("that" in tokens1)
        # second iteration should fetch from the cache
        with self.assertLogs(level="INFO") as cm2:
            ids2, tokens2 = crossmap.targets_features()
        self.assertTrue("cache" in str(cm2.output))
        self.assertEqual(ids1, ids2)
        self.assertEqual(tokens1, tokens2)
        # both results should have all tokens
        self.assertTrue("compl" in tokens1)
        self.assertTrue("compl" in tokens2)

    def test_target_tokens_unique(self):
        """Target tokens should be unique"""

        crossmap = Crossmap(config_plain)
        crossmap_dir = crossmap.settings.data_dir
        ids, tokens = crossmap.targets_features()
        # output should be a set (i.e. unique strings)
        self.assertTrue(type(tokens) is dict)
        # content on disk should contain same number of items (plus header)
        toks_file = join(crossmap_dir, "crossmap0-target-features.tsv")
        with open(toks_file, "rt") as f:
            lines = f.readlines()
        self.assertEqual(len(lines)-1, len(tokens))

    def test_feature_map(self):
        """Target tokens can exclude certain elements"""

        crossmap = Crossmap(config_exclude)
        ids, counts = crossmap.targets_features()
        features = crossmap._feature_map(counts.keys())
        self.assertTrue(len(features), len(counts))
        self.assertEqual(set(counts.keys()), set(features.keys()))


class CrossmapBuildTests(unittest.TestCase):
    """Building a crossmap object"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_target_matrix(self):
        """Construct a sparse data object from target documents"""

        crossmap = Crossmap(config_plain)
        crossmap_dir = crossmap.settings.data_dir
        crossmap.build()
        data_file = join(crossmap_dir, "crossmap0-data")
        ids_file = join(crossmap_dir, "crossmap0-ids")
        self.assertTrue(exists(data_file))
        self.assertTrue(exists(ids_file))
        self.assertGreater(crossmap.datum("A", "Alice"), 1)
        self.assertGreater(crossmap.datum("C", "Catherine"), 1)
        self.assertEqual(crossmap.datum("A", "Catherine"), 0)

    def test_document_features_all(self):
        """extract additional features from documents"""

        crossmap = Crossmap(config_plain)
        crossmap.tokenizer.min_length = 0
        # scan documents, find documents that overlap with tokens A, B
        doc_features = crossmap.document_features(set(["a", "b"]), 100)
        # documents have 7 letters in total
        self.assertEqual(len(doc_features), 7)

    def test_top_document_features(self):
        """extract additional features from documents"""

        crossmap = Crossmap(config_plain)
        crossmap.tokenizer.min_length = 0
        # scan documents, find documents that overlap with tokens A, B
        doc_features = crossmap.document_features(set(["a", "b"]), 4)
        # documents have 7 letters in total, but the four top ones are a-d
        # a-d are in documents that overlap with a, b
        self.assertEqual(doc_features, set(["a", "b", "c", "d"]))


class CrossmapPredictTests(unittest.TestCase):
    """Mapping new objects onto targets"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap0")
        cls.crossmap = Crossmap(config_plain)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_embedding_exists(self):
        """internal check: class setup build a crossmap object"""
        self.assertEqual(self.crossmap.settings.name, "crossmap0")

    def test_self_predict(self):
        """predicting items from within the dataset should map onto themselves"""

        tokens = self.crossmap.tokenizer.tokenize(dataset_file)
        result = self.crossmap.predict(dataset_file)
        self.assertEqual(len(result), len(tokens))
        for k,v in result.items():
            self.assertEqual(k, v, "all items should match to themselves")

