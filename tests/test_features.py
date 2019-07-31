'''Tests for turning documents into tokens
'''

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.features import feature_map
from crossmap.features import read_feature_map, write_feature_map
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file = join(data_dir, "config-simple.yaml")
config_constant_file = join(data_dir, "config-constant.yaml")


class CrossmapFeatureMapTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        self.settings = CrossmapSettings(config_file, create_dir=True)
        self.cache_file = self.settings.tsv_file("feature-map")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_feature_map_wo_cache(self):
        """scan for features in targets and documents"""

        self.assertFalse(exists(self.cache_file))
        map = feature_map(self.settings, False)
        self.assertFalse(exists(self.cache_file))
        self.assertGreater(len(map), 2)
        self.assertTrue("bob" in map)
        self.assertTrue("g" in map)
        # all items in map should be distinct
        indexes = [v[0] for k, v in map.items()]
        weights = [v[1] for k, v in map.items()]
        self.assertEqual(max(indexes), len(map)-1)
        self.assertGreater(min(weights), 0, "all weights should be positive")

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

    def test_skip_documents(self):
        """scan for features in targets, but not documents"""

        # when number of features is limited, there is no need
        # to scan documents. All features come from targets.
        self.settings.features.max_number=20
        with self.assertLogs(level="INFO") as cm:
            map = feature_map(self.settings, False)
        self.assertTrue("bob" in map)
        self.assertFalse("g" in map)
        self.assertLess(len(map), 50)

    def test_skipping_partial_documents(self):
        """scan for features in targets, but not documents"""

        # with an intermediate number of required features,
        # some features will come from targets, some from documents.
        self.settings.features.max_number = 50
        with self.assertLogs(level="INFO") as cm:
            map = feature_map(self.settings, False)
        self.assertTrue("bob" in map)
        # map will have exactly the max features
        self.assertEqual(len(map), 50)
        self.assertTrue("g" in map)
        self.assertFalse("M" in map)

    def test_weights(self):
        """scan for features in targets, but not documents"""

        # compute two maps using different weighting
        with self.assertLogs(level="INFO") as cm:
            self.settings.features.weighting = "constant"
            map_const = feature_map(self.settings, False)
            self.settings.features.weighting = "ic"
            map_ic = feature_map(self.settings, False)
        self.assertEqual(len(map_const), len(map_ic))
        # constant map has all the weights equal to 1
        for k,v in map_const.items():
            self.assertEqual(v[1], 1)
        # information content map has certain features with less weight
        self.assertLess(map_ic["with"][1], map_ic["alice"][1])
        self.assertLess(map_ic["with"][1], map_ic["uniqu"][1])
        self.assertEqual(map_ic["uniqu"][1], map_ic["token"][1])


class CrossmapFeatureMapWeightingTests(unittest.TestCase):
    """Turning text data into tokens with Log weighting"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_constant")

    def test_ic_log1(self):

        with self.assertLogs(level="WARNING") as cm1:
            settings = CrossmapSettings(config_constant_file,
                                        create_dir=True)
        with self.assertLogs(level="INFO") as cm2:
            settings.features.weighting = "ic"
            map_const = feature_map(settings, False)
        # all features should have >0 weights
        for k, v in map_const.items():
            kmsg = "feature "+str(k)+" should have weight >0"
            self.assertGreater(v[1], 0, kmsg)


class CrossmapFeatureMapIOTests(unittest.TestCase):
    """reading and writing feature-map tables"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        self.settings = CrossmapSettings(config_file, create_dir=True)

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_write_read(self):
        """read and write a custom-made object"""
        map = dict(a=(0,1), b=(1,0.5))
        map_file = self.settings.tsv_file("feature-map")
        write_feature_map(map, map_file)
        map2 = read_feature_map(map_file)
        self.assertEqual(len(map2), len(map))
        self.assertEqual(map2["a"], map["a"])
        self.assertEqual(map2["b"], map["b"])

