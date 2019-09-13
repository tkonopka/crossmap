"""Tests for parsing settings
"""

import unittest
from os.path import join
from crossmap.settings import CrossmapSettings
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_file = join(data_dir, "config-simple.yaml")
custom_config_file = join(data_dir, "config.yaml")
config_no_target_file = join(data_dir, "config-no-targets.yaml")
config_no_documents_file = join(data_dir, "config-no-documents.yaml")
config_typo_file = join(data_dir, "config-typo-target.yaml")
config_tokens_file = join(data_dir, "config-tokens.yaml")
config_server_file = join(data_dir, "config-server.yaml")
config_weighting_file = join(data_dir, "config-weighting.yaml")

documents_file = join(data_dir, "documents.yaml")

include_file = join(data_dir, "include.txt")
exclude_file = join(data_dir, "exclude.txt")
exclude_file2 = join(data_dir, "exclude_2.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapSettingsTests(unittest.TestCase):
    """Recording settings for a crossmap analysis"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "default0")
        remove_crossmap_cache(data_dir, "no_universe")
        remove_crossmap_cache(data_dir, "no_targets")
        remove_crossmap_cache(data_dir, "crossmap")

    def test_init_dir(self):
        """Configure with just a directory"""

        result = CrossmapSettings(data_dir)
        self.assertEqual(result.dir, data_dir)
        self.assertEqual(result.file, "crossmap.yaml")
        self.assertTrue(result.valid)

    def test_init_file(self):
        """Configure with valid configuration file"""

        result = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertEqual(result.dir, data_dir)
        self.assertEqual(result.file, "config.yaml")
        self.assertTrue(result.valid)

    def test_init_missing_file(self):
        """Attempt to configure with a non-existent file"""

        with self.assertLogs(level='ERROR'):
            result = CrossmapSettings(join(data_dir, "missing.yaml"))
            self.assertFalse(result.valid)

    def test_init_no_target(self):
        """Attempt to configure with a configuration file without target"""

        with self.assertLogs(level='ERROR'):
            result = CrossmapSettings(config_no_target_file)
            self.assertFalse(result.valid)

    def test_init_no_documents(self):
        """Attempt to configure with a configuration file without docs"""

        with self.assertLogs(level='WARNING'):
            result = CrossmapSettings(config_no_documents_file)
            self.assertTrue(result.valid)

    def test_warnings_missing_files(self):
        """Attempt to configure with a configuration with a typo"""

        with self.assertLogs(level='WARNING'):
            result = CrossmapSettings(config_typo_file)
        # one target file is valid, so the overall config is valid
        self.assertTrue(result.valid)

    def test_full_paths(self):
        """Extract project file paths"""

        settings = CrossmapSettings(config_file)
        result = settings.files("documents")
        self.assertEqual(len(result), 1)
        self.assertEqual(result, [documents_file])

    def test_full_paths_docs_targets(self):
        """Extract both document and target file paths"""

        settings = CrossmapSettings(config_file)
        result = settings.files(["documents", "targets"])
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result), set([dataset_file, documents_file]))

    def test_warning_upon_faulty_file_retrieval(self):
        """Retrieving a non-canonical file type gives warning"""

        settings = CrossmapSettings(config_file)
        with self.assertLogs(level='WARNING') as cm:
            settings.files(["documents", "badname"])
        self.assertTrue("badname" in str(cm.output))

    def test_tsv_file(self):
        """settings object can create a file path to a tsv file"""
        settings = CrossmapSettings(config_file)
        result = settings.tsv_file("abc")
        cs = "crossmap_simple"
        self.assertEqual(result, join(data_dir, cs, cs + "-abc.tsv"))

    def test_pickle_file(self):
        """settings object can create a file path to a pickle object"""
        settings = CrossmapSettings(config_file)
        result = settings.pickle_file("abc")
        cs = "crossmap_simple"
        self.assertEqual(result, join(data_dir, cs, cs + "-abc"))

    def test_str(self):
        """summarize the settings in a single string"""
        settings = CrossmapSettings(config_file)
        self.assertTrue("simple" in str(settings))

    def test_validate_weights(self):
        """validation can detect misspecified feature weighting scheme"""
        with self.assertLogs(level="WARNING") as cm:
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

        result = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertEqual(result.features.max_number, 200)

    def test_aux_weight(self):
        """configure weight assigned to auxiliary data fields"""

        result = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertEqual(result.features.aux_weight[0], 0.4)
        self.assertEqual(result.features.aux_weight[1], 0.2)

    def test_str(self):
        """summarize settings in a string"""

        settings = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertTrue("0.4" in str(settings.features))
        self.assertTrue("0.2" in str(settings.features))


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
