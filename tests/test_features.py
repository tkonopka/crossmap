"""
Tests for turning documents into tokens
"""

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.features import feature_map, CrossmapFeatures
from crossmap.features import read_feature_map, write_feature_map
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file = join(data_dir, "config-simple.yaml")
config_constant_file = join(data_dir, "config-constant.yaml")


class CrossmapFeatureMapTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        self.settings = CrossmapSettings(config_file, create_dir=True)
        self.cache_file = self.settings.tsv_file("feature-map")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_feature_map_unique_ids(self):
        """features in targets and documents must have unique ids"""

        map = feature_map(self.settings)
        # map should be a dict from strings into (index, weight)
        all_indexes = set([v[0] for k,v in map.items()])
        self.assertEqual(len(all_indexes), len(map))

    def test_skipping_partial_documents(self):
        """scan for features in targets, but not documents"""

        # with an intermediate number of required features,
        # some features will come from targets, some from documents.
        self.settings.features.max_number = 50
        with self.assertLogs(level="INFO"):
            map = feature_map(self.settings)
        self.assertTrue("bob" in map)
        # map will have exactly the max features
        self.assertEqual(len(map), 50)
        self.assertTrue("g" in map)
        self.assertFalse("M" in map)

    def test_weights_ic(self):
        """weights using constant and ic scaling"""

        # compute maps using different weightings
        with self.assertLogs(level="INFO"):
            self.settings.features.weighting = [1,0]
            map_const = feature_map(self.settings)
            self.settings.features.weighting = [0, 1]
            map_ic = feature_map(self.settings)
            self.settings.features.weighting = [1, 1]
            map_mid = feature_map(self.settings)
        # maps should all contain same features, i.e. equal length
        self.assertEqual(len(map_const), len(map_ic))
        self.assertEqual(len(map_const), len(map_mid))
        # constant map has all the weights equal to 1
        for k, v in map_const.items():
            self.assertEqual(v[1], 1)
        # information content map has certain features with less weight
        with_ic = map_ic["with"][1]
        with_const = map_const["with"][1]
        self.assertLess(with_ic, map_ic["alice"][1])
        self.assertLess(with_ic, map_ic["uniqu"][1])
        self.assertEqual(map_ic["uniqu"][1], map_ic["token"][1])
        # Because mixed map has high coefficient for both constant and ic,
        # all values should be higher than in either constant or ic maps
        with_mid = map_mid["with"][1]
        self.assertGreater(with_mid, with_ic)
        self.assertGreater(with_mid, with_const)

    def test_feature_map_min_count(self):
        """only use features present in a miniaml num of docs"""

        with self.assertLogs(level="INFO"):
            self.settings.features.max_number = 1000
            self.settings.features.min_count = 1
            map1 = feature_map(self.settings)
            self.settings.features.min_count = 2
            map2 = feature_map(self.settings)
        # map will have exactly the max features
        self.assertTrue("abcde" in map1)
        self.assertFalse("abcde" in map2)


class CrossmapFeatureMapWeightingTests(unittest.TestCase):
    """Assigning weights to tokens based on their frequencies"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_constant")

    def test_nonzero_weight(self):
        """all features must have nonzero weight"""

        # use a configuration with log weights
        settings = CrossmapSettings(config_constant_file, create_dir=True)
        with self.assertLogs(level="INFO") as cm:
            settings.features.weighting = [0, 1]
            map_const = feature_map(settings)
        self.assertTrue("Extracting" in str(cm.output))
        # all features should have >0 weights
        for k, v in map_const.items():
            kmsg = "feature "+str(k)+" should have weight >0"
            self.assertGreater(v[1], 0, kmsg)


class CrossmapFeatureMapIOTests(unittest.TestCase):
    """reading and writing feature-map tables"""

    def setUp(self):
        self.settings = CrossmapSettings(config_file, create_dir=True)

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_write_read(self):
        """read and write a custom-made object"""
        map = dict(a=(0,1), b=(1,0.5))
        map_file = self.settings.tsv_file("feature-map")
        write_feature_map(map, self.settings)
        map2 = read_feature_map(map_file)
        self.assertEqual(len(map2), len(map))
        self.assertEqual(map2["a"], map["a"])
        self.assertEqual(map2["b"], map["b"])


class CrossmapFeaturesClassTests(unittest.TestCase):
    """using the class to save features in database"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_saves_disk_file(self):
        """scan for features and record in cache"""

        settings = CrossmapSettings(config_file, create_dir=True)
        cache_file = settings.tsv_file("feature-map")
        self.assertFalse(exists(cache_file))
        # run the feature extraction, should create a cache file
        with self.assertLogs(level="INFO") as cm1:
            CrossmapFeatures(settings)
        self.assertTrue(exists(cache_file))
        self.assertTrue("Saving" in str(cm1.output))

