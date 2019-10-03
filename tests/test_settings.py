"""Tests for parsing settings
"""

import unittest
from os.path import join
from crossmap.settings import CrossmapSettings
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")

# good configurations
config_file = join(data_dir, "config-simple.yaml")
config_complete_file = join(data_dir, "config-complete.yaml")
config_tokens_file = join(data_dir, "config-tokens.yaml")
config_single_file = join(data_dir, "config-single.yaml")

# invalid or problematic configurations
config_no_data_file = join(data_dir, "config-no-data.yaml")
config_nonexistent_file = join(data_dir, "config-nonexistent.yaml")

# configuration that trigger sub-parsers
config_server_file = join(data_dir, "config-server.yaml")
config_weighting_file = join(data_dir, "config-weighting.yaml")

# paths to data files
documents_file = join(data_dir, "documents.yaml")
dataset_file = join(data_dir, "dataset.yaml")
features_file = join(data_dir, "featuremap.tsv")


class CrossmapSettingsErrorTests(unittest.TestCase):
    """detecting invalid attempts to set up settings"""

    def test_init_missing_file(self):
        """Attempt to configure with a non-existent file"""

        with self.assertLogs(level='ERROR'):
            result = CrossmapSettings(join(data_dir, "missing.yaml"))
            self.assertFalse(result.valid)

    def test_init_no_data(self):
        """Attempt to configure with a configuration file without any data"""

        with self.assertLogs(level='ERROR'):
            result = CrossmapSettings(config_no_data_file)
            self.assertFalse(result.valid)

    def test_warnings_nonexistent_files(self):
        """Attempt to configure with a configuration with a typo"""

        with self.assertLogs(level='WARNING'):
            result = CrossmapSettings(config_nonexistent_file)
        # one target file is valid, so the overall config is valid
        self.assertTrue(result.valid)


class CrossmapSettingsDirTests(unittest.TestCase):
    """intialize based only a directory name and file crossmap.yaml"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_default")

    def test_init_dir(self):
        """Configure with just a directory"""

        result = CrossmapSettings(data_dir)
        self.assertEqual(result.dir, data_dir)
        self.assertEqual(result.file, "crossmap.yaml")
        self.assertTrue(result.valid)


class CrossmapSettingsSimpleTests(unittest.TestCase):
    """parsing settings from a simple file"""

    @classmethod
    def setUpClass(cls):
        cls.settings = CrossmapSettings(config_file)

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_default")

    def test_full_paths_data(self):
        """Extract project file paths"""

        settings = self.settings
        self.assertEqual(len(settings.data_files), 2)
        self.assertEqual(settings.data_files["documents"], documents_file)
        self.assertEqual(settings.data_files["targets"], dataset_file)

    def test_full_paths_featuremap(self):
        """simple configuration does not specify a feature map file"""

        settings = self.settings
        self.assertEqual(settings.features.map_file, None)

    def test_warning_upon_faulty_file_retrieval(self):
        """Retrieving a non-canonical file type gives warning"""

        with self.assertRaises(Exception):
            self.settings.data["badname"]

    def test_tsv_file(self):
        """settings object can create a file path to a tsv file"""

        result = self.settings.tsv_file("abc")
        cs = "crossmap_simple"
        self.assertEqual(result, join(data_dir, cs, cs + "-abc.tsv"))

    def test_pickle_file(self):
        """settings object can create a file path to a pickle object"""

        result = self.settings.pickle_file("abc")
        cs = "crossmap_simple"
        self.assertEqual(result, join(data_dir, cs, cs + "-abc"))

    def test_str(self):
        """summarize the settings in a single string"""

        self.assertTrue("simple" in str(self.settings))


class CrossmapSettingsCompleteTests(unittest.TestCase):
    """parsing settings from a complete file with many options"""

    @classmethod
    def setUpClass(cls):
        cls.settings = CrossmapSettings(config_complete_file)

    @classmethod
    def tearDown(cls):
        remove_crossmap_cache(data_dir, "crossmap_complete")

    def test_init_file(self):
        """Configure with valid configuration file"""

        self.assertEqual(self.settings.dir, data_dir)
        self.assertEqual(self.settings.file, "config-complete.yaml")
        self.assertTrue(self.settings.valid)


class CrossmapSettingsDiffusionTests(unittest.TestCase):
    """parsing settings for diffusion"""

    def setUp(self):
        self.settings = CrossmapSettings(config_complete_file)

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_complete")

    def test_threshold(self):
        """file set nonzero diffiusion threshold"""

        d = self.settings.diffusion
        self.assertGreater(d.threshold, 0.0)


class CrossmapSettingsMiscTests(unittest.TestCase):
    """parsing settings from misc files"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_single")
        remove_crossmap_cache(data_dir, "crossmap_complete")

    def test_init_single(self):
        """a configuration file can specify a single dataset"""

        result = CrossmapSettings(config_single_file)
        self.assertTrue(result.valid)

    def test_validate_weights(self):
        """validation can detect misspecified feature weighting scheme"""

        with self.assertLogs(level="WARNING"):
            settings = CrossmapSettings(config_weighting_file)
            settings._validate()


class CrossmapFeaturesSettingsTests(unittest.TestCase):
    """Recording settings for handling features within crossmap analysis"""

    def test_default_features(self):
        """By default max number of features is 0"""

        result = CrossmapSettings(data_dir)
        self.assertEqual(result.features.max_number, 0)

    def test_max_features(self):
        """configure number of features in data vectors"""

        result = CrossmapSettings(config_complete_file)
        self.assertEqual(result.features.max_number, 200)

    def test_weighting(self):
        """configure weight assigned to auxiliary data fields"""

        result = CrossmapSettings(config_complete_file)
        self.assertEqual(result.features.weighting[0], 0.5)
        self.assertEqual(result.features.weighting[1], 1)

    def test_str(self):
        """summarize settings in a string"""

        settings = CrossmapSettings(config_complete_file)
        self.assertTrue("0.5" in str(settings.features))

    def test_file(self):
        """declare a file source for features"""

        settings = CrossmapSettings(config_complete_file)
        self.assertEqual(settings.features.map_file, features_file)


class CrossmapKmerSettingsTests(unittest.TestCase):
    """Settings related to tokenizing documents"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_tokens")

    def test_k_alphabet(self):
        """settings are transfered from file into settings object"""

        settings = CrossmapSettings(config_tokens_file)
        self.assertEqual(settings.tokens.k, 6)
        # custom alphabet has consonants but not vowels
        self.assertTrue("b" in settings.tokens.alphabet)
        self.assertTrue("w" in settings.tokens.alphabet)
        self.assertFalse("e" in settings.tokens.alphabet)
        self.assertFalse("i" in settings.tokens.alphabet)

    def test_str(self):
        """summarize settings in a string"""
        settings = CrossmapSettings(config_tokens_file)
        settings.tokens.k = 241
        self.assertTrue("241" in str(settings.tokens))


class CrossmapServerSettingsTests(unittest.TestCase):
    """Settings related to tokenizing documents"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_server")

    def test_ports(self):
        """settings are transferred from file into settings object"""

        settings = CrossmapSettings(config_server_file)
        self.assertEqual(settings.server.api_port, 8080)
        self.assertEqual(settings.server.ui_port, 8081)

    def test_str(self):
        """summarize settings in a string"""
        settings = CrossmapSettings(config_server_file)
        self.assertTrue("8081" in str(settings.server))

