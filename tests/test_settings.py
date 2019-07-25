'''Tests for parsing settings
'''

import unittest
from os.path import join
from crossmap.crossmap import CrossmapSettings
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_file = join(data_dir, "crossmap.yaml")
custom_config_file = join(data_dir, "config.yaml")
config_no_target_file = join(data_dir, "config-no-targets.yaml")
config_no_documents_file = join(data_dir, "config-no-documents.yaml")
config_typo_file = join(data_dir, "config-typo-target.yaml")

documents_file = join(data_dir, "documents.yaml")

include_file = join(data_dir, "include.txt")
exclude_file = join(data_dir, "exclude.txt")
exclude_file2 = join(data_dir, "exclude_2.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapSettingsTests(unittest.TestCase):
    """Turning text data into tokens"""

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
        self.assertFalse(result.valid)

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

    def test_default_features(self):
        """By default max number of features is 0"""

        result = CrossmapSettings(data_dir)
        self.assertEqual(result.max_features, 0)

    def test_max_features(self):
        """configure number of features for embedding"""

        result = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertEqual(result.max_features, 200)

    def test_uamp_settings(self):
        """set umap settings via the configuration"""

        result = CrossmapSettings(custom_config_file)
        self.assertEqual(result.umap.metric, "euclidean")
        self.assertEqual(result.umap.n_neighbors, 5)
        self.assertEqual(result.umap.n_components, 1)

