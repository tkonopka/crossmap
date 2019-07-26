'''Tests for turning documents into tokens
'''

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.feature_map import feature_map
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_file = join(data_dir, "crossmap.yaml")


class CrossmapFeatureMapTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        self.settings = CrossmapSettings(config_file)
        self.settings.max_features = 1000
        self.cache_file = self.settings.tsv_file("feature-map")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_feature_map_wo_cache(self):
        """scan for features in targets and documents"""

        self.assertFalse(exists(self.cache_file))
        map = feature_map(self.settings, False)
        self.assertFalse(exists(self.cache_file))
        self.assertGreater(len(map), 2)
        self.assertTrue("bob" in map)
        self.assertTrue("g" in map)
        # all items in map should be distinct
        v = [v for k,v in map.items()]
        self.assertEqual(max(v), len(map)-1)

    def test_feature_map_w_cache(self):
        """scan for features and record in cache"""

        self.assertFalse(exists(self.cache_file))
        # run the map, this should log and create a cache file
        with self.assertLogs(level="INFO") as cm1:
            map = feature_map(self.settings, True)
        self.assertTrue(exists(self.cache_file))
        self.assertTrue("Saving" in str(cm1.output))
        # running again should use the cache value
        with self.assertLogs(level="INFO") as cm2:
            map = feature_map(self.settings, True)
        self.assertTrue(exists(self.cache_file))
        self.assertTrue("Reading" in str(cm2.output))
        self.assertFalse("Extracting" in str(cm2.output))
        # but can ignore cache file and extract from scratch
        with self.assertLogs(level="INFO") as cm3:
            map = feature_map(self.settings, False)
        self.assertFalse("Reading" in str(cm3.output))
        self.assertTrue("Extracting" in str(cm3.output))

    def test_skipping_documents(self):
        """scan for features in targets, but not documents"""

        self.settings.max_features=20
        with self.assertLogs(level="INFO") as cm:
            map = feature_map(self.settings, False)
        self.assertTrue("bob" in map)
        self.assertFalse("g" in map)
        self.assertTrue("Skipping" in str(cm.output))
        self.assertTrue("already" in str(cm.output))

    def test_skipping_partial_documents(self):
        """scan for features in targets, but not documents"""

        self.settings.max_features = 50
        with self.assertLogs(level="INFO") as cm:
            map = feature_map(self.settings, False)
        self.assertTrue("bob" in map)
        # map will have exactly the max features
        self.assertEqual(len(map), 50)
        self.assertTrue("g" in map)
        self.assertFalse("M" in map)
