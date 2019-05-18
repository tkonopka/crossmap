'''Tests for turning datasets into tokens

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
        # crossmap0 is a string in the config.yaml file
        self.assertEqual(crossmap.settings.name, "crossmap0")

    def test_target_tokens(self):
        """Extract tokens from target objects"""

        crossmap = Crossmap(config_plain)
        # token cache should not exist
        toks_file = join(data_dir, "crossmap0-target-features.tsv")
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
        ids, tokens = crossmap.targets_features()
        # output should be a set (i.e. unique strings)
        self.assertTrue(type(tokens) is set)
        # content on disk should contain same number of items (plus header)
        toks_file = join(data_dir, "crossmap0-target-features.tsv")
        with open(toks_file, "rt") as f:
            lines = f.readlines()
        self.assertEqual(len(lines)-1, len(tokens))

    #def test_target_tokens_exclude(self):
    #    """Target tokens can exclude certain elements"""
    #    crossmap = Crossmap(config_exclude)
    #    ids, tokens = crossmap.targets_features()
    #    self.assertFalse("that" in tokens)

    def test_feature_map(self):
        """Target tokens can exclude certain elements"""

        crossmap = Crossmap(config_exclude)
        ids, tokens = crossmap.targets_features()
        features = crossmap.feature_map(tokens)
        self.assertTrue(len(features), len(tokens))
        self.assertEqual(tokens, set(features.keys()))


class CrossmapBuildTests(unittest.TestCase):
    """Building a crossmap object"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_target_matrix(self):
        """Construct a sparse data object from target documents"""

        crossmap = Crossmap(config_plain)
        crossmap.build()
        data_file = join(data_dir, "crossmap0-data")
        ids_file = join(data_dir, "crossmap0-ids")
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