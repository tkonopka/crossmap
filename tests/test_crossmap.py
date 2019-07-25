'''Tests for mapping across datasets using token similarities
'''

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "crossmap.yaml")
config_exclude = join(data_dir, "crossmap-exclude.yaml")

include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapInitTests(unittest.TestCase):
    """Special cases for initialization"""

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

    def test_exclude(self):
        """Target tokens can exclude certain elements"""

        crossmap = Crossmap(config_exclude)
        ids, counts = crossmap.targets_features()
        features = crossmap._feature_map(counts.keys())
        self.assertTrue(len(features), len(counts))
        self.assertEqual(set(counts.keys()), set(features.keys()))


class CrossmapBuildTests(unittest.TestCase):
    """Building a crossmap object"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap0")
        cls.crossmap = Crossmap(config_plain)

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_target_tokens(self):
        """Build extracts tokens from target objects"""

        crossmap_dir = self.crossmap.settings.data_dir
        toks_file = join(crossmap_dir, "crossmap0-target-features.tsv")
        with self.assertLogs(level="INFO") as cm1:
            ids1, tokens = self.crossmap.targets_features()
        self.assertTrue(exists(toks_file))
        self.assertTrue("features" in str(cm1.output))
        self.assertTrue("with" in tokens)
        self.assertTrue("start" in tokens)
        self.assertTrue("that" in tokens)
        self.assertTrue("compl" in tokens)

    def test_target_tokens_unique(self):
        """Target tokens should be unique"""

        crossmap_dir = self.crossmap.settings.data_dir
        ids, tokens = self.crossmap.targets_features()
        # output should be a set (i.e. unique strings)
        self.assertTrue(type(tokens) is dict)
        # content on disk should contain same number of items (plus header)
        toks_file = join(crossmap_dir, "crossmap0-target-features.tsv")
        with open(toks_file, "rt") as f:
            lines = f.readlines()
        self.assertEqual(len(lines)-1, len(tokens))

    def test_target_matrix(self):
        """Build constructs a sparse data object from target documents"""

        crossmap_dir = self.crossmap.settings.data_dir
        data_file = join(crossmap_dir, "crossmap0-data")
        ids_file = join(crossmap_dir, "crossmap0-ids")
        self.assertTrue(exists(data_file))
        self.assertTrue(exists(ids_file))
        self.assertGreater(self.crossmap.datum("A", "Alice"), 1)
        self.assertGreater(self.crossmap.datum("C", "Catherine"), 1)
        self.assertEqual(self.crossmap.datum("A", "Catherine"), 0)

