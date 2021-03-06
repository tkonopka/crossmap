"""
Tests for parsing sub-settings (features, server, tokens, etc.)

(Some of these are only stubs; they can be expanded when the
classes start performing stronger validation)
"""

import unittest
import yaml
from os.path import join, exists
from crossmap.subsettings import \
    CrossmapDataSettings, \
    CrossmapLoggingSettings, \
    CrossmapFeatureSettings, \
    CrossmapTokenSettings, \
    CrossmapIndexingSettings, \
    CrossmapServerSettings, \
    CrossmapDiffusionSettings, \
    CrossmapCacheSettings


class CrossmapSettingsDataTests(unittest.TestCase):
    """parsing settings for data collections"""

    def test_find_files_from_filenames(self):
        """specify data collection paths based on filenames only"""
        simple_path = "documents.yaml"
        result = CrossmapDataSettings({"docs": simple_path},
                                      data_dir=join("tests", "testdata"))
        self.assertTrue(exists(result.collections["docs"]))

    def test_find_files_from_dirpath(self):
        """specify data collections based on relative paths"""
        rel_path = join("testdata", "documents.yaml")
        result = CrossmapDataSettings({"docs": rel_path},
                                      data_dir=join("tests"))
        self.assertTrue(exists(result.collections["docs"]))

    def test_str(self):
        """str captures all files and default collection"""
        result = CrossmapDataSettings({"docs": "documents.yaml"},
                                      data_dir=join("tests", "testdata"))
        self.assertTrue("docs" in str(result))


class CrossmapSettingsDiffusionTests(unittest.TestCase):
    """parsing settings for diffusion"""

    def setUp(self):
        self.default = CrossmapDiffusionSettings()
        self.custom = CrossmapDiffusionSettings({"threshold": 0.5, "passes": 4})

    def test_threshold(self):
        """file set nonzero diffusion threshold"""

        self.assertEqual(self.default.threshold, 0)
        self.assertGreater(self.custom.threshold, 0.0)

    def test_passes(self):
        """file set nonzero diffusion threshold"""

        self.assertEqual(self.default.num_passes, 2)
        self.assertEqual(self.custom.num_passes, 4)

    def test_str(self):
        """can construct a str representation"""

        self.assertTrue("diffusion" in str(self.default))
        self.assertTrue("pass" in str(self.default))


class CrossmapFeaturesSettingsTests(unittest.TestCase):
    """Recording settings for handling features within crossmap analysis"""

    def setUp(self):
        self.default = CrossmapFeatureSettings()
        custom = {"data": "dataset.yaml",
                  "max_number": 200,
                  "min_count": 2,
                  "decoy": 0,
                  "weighting": [0.5, 0.5],
                  "aux": [1, 0.2]}
        self.custom = CrossmapFeatureSettings(custom)

    def test_features_max_number(self):
        """By default max number of features is 0"""

        self.assertEqual(self.default.max_number, 0)
        self.assertEqual(self.custom.max_number, 200)

    def test_features_min_count(self):
        """By default min_count for a features is 1"""

        self.assertEqual(self.default.min_count, 1)
        self.assertEqual(self.custom.min_count, 2)

    def test_weighting(self):
        """configure weight assigned to auxiliary data fields"""

        self.assertEqual(self.default.weighting[0], 1)
        self.assertEqual(self.custom.weighting[1], 0.5)

    def test_map_file(self):
        """declare a file source for features"""

        self.assertEqual(self.default.map_file, None)
        with_map = CrossmapFeatureSettings({"map": "table.tsv"}, "crossmap")
        self.assertEqual(with_map.map_file, join("crossmap", "table.tsv"))

    def test_data_files(self):
        """declare a yaml collection source for feature extraction."""

        self.assertEqual(self.default.data_files, {})
        custom_data = {"custom": "documents.yaml"}
        with_data = CrossmapFeatureSettings({"data": custom_data}, "crossmap")
        self.assertEqual(with_data.data_files,
                         {"custom": join("crossmap", "documents.yaml")})

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("0.5" in str(self.custom))


class CrossmapTokenSettingsTests(unittest.TestCase):
    """Settings related to tokenizing documents"""

    def setUp(self):
        self.default = CrossmapTokenSettings()
        self.custom = CrossmapTokenSettings({"k": 8, "alphabet": "abcde"})

    def test_k(self):
        """length of kmers"""

        self.assertListEqual(self.default.k, [5, 10])
        self.assertListEqual(self.custom.k, [8, 16])

    def test_alphabet(self):
        """settings are transfered from file into settings object"""

        # default alphabet
        self.assertEqual(self.default.alphabet, None)
        # custom alphabet
        self.assertTrue("e" in self.custom.alphabet)
        self.assertFalse("i" in self.custom.alphabet)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("abc" in str(self.custom))


class CrossmapIndexingSettingsTests(unittest.TestCase):
    """Settings related to quality of index build and kNN search"""

    def setUp(self):
        self.default = CrossmapIndexingSettings()
        self.custom = CrossmapIndexingSettings({"build_quality": 50, "search_quality": 100})

    def test_build_quality(self):
        """parsing build quality"""

        self.assertEqual(self.default.build_quality, 200)
        self.assertEqual(self.custom.build_quality, 50)

    def test_search_quality(self):
        """parsing search quality"""

        self.assertEqual(self.default.search_quality, 200)
        self.assertEqual(self.custom.search_quality, 100)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("quality" in str(self.custom))


class CrossmapServerSettingsTests(unittest.TestCase):
    """Settings related to configuring servers"""

    def setUp(self):
        ports = {"api_port": 8080, "ui_port": 8081, "db_port": 8082}
        self.custom = CrossmapServerSettings(ports)

    def test_ports(self):
        """settings extract port numbers"""

        self.assertEqual(self.custom.api_port, 8080)
        self.assertEqual(self.custom.ui_port, 8081)
        self.assertEqual(self.custom.db_port, 8082)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("8081" in str(self.custom))


class CrossmapLoggingSettingsTests(unittest.TestCase):
    """Settings related to configuring logging"""

    def setUp(self):
        self.default = CrossmapLoggingSettings()
        custom = {"level": "INFO", "progress": 100}
        self.custom = CrossmapLoggingSettings(custom)

    def test_level(self):
        """settings logging detail"""

        self.assertEqual(self.default.level, "WARNING")
        self.assertEqual(self.custom.level, "INFO")

    def test_progress_interval(self):
        """settings for how often to report progress"""

        self.assertGreater(self.default.progress, 1000)
        self.assertEqual(self.custom.progress, 100)

    def test_str(self):
        """settings can be displayed as a yaml string"""

        # string format
        self.assertTrue("level" in str(self.custom))
        self.assertTrue("progress" in str(self.custom))
        self.assertTrue("INFO" in str(self.custom))
        self.assertTrue("WARNING" in str(self.default))
        # yaml format
        parsed_custom = yaml.load(str(self.custom), yaml.CBaseLoader)
        self.assertTrue("logging" in parsed_custom)


class CrossmapCacheTests(unittest.TestCase):
    """parsing settings for caching items from the database"""

    def setUp(self):
        self.default = CrossmapCacheSettings()
        custom = {"counts": 256, "ids": 128,
                  "titles": 128, "data": 1024}
        self.custom = CrossmapCacheSettings(custom)

    def test_sizes(self):
        """parsing cache sizes"""

        self.assertEqual(self.custom.counts, 256)
        self.assertEqual(self.custom.ids, 128)
        self.assertEqual(self.custom.titles, 128)
        self.assertEqual(self.custom.data, 1024)

    def test_str(self):
        """settings can be displayed in yaml string"""

        # string format
        custom_str = str(self.custom)
        self.assertTrue("256" in custom_str and "1024" in custom_str)
        self.assertTrue("data" in custom_str and "counts" in custom_str)
        # yaml format
        parsed_custom = yaml.load(custom_str, yaml.CBaseLoader)
        self.assertTrue("cache" in parsed_custom)
        self.assertTrue("counts" in parsed_custom["cache"])

