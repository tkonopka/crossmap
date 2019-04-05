'''Tests for parsing settings

@author: Tomasz Konopka
'''

import unittest
from os.path import join
from crossmap.crossmap import CrossmapSettings

data_dir = join("tests", "testdata")
config_file = join(data_dir, "crossmap.yaml")
custom_config_file = join(data_dir, "config.yaml")
config_no_target_file = join(data_dir, "config-no-targets.yaml")
config_no_universe_file = join(data_dir, "config-no-universe.yaml")

include_file = join(data_dir, "test_include.txt")
exclude_file = join(data_dir, "test_exclude.txt")
exclude_file2 = join(data_dir, "test_exclude_2.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapSettingsTests(unittest.TestCase):
    """Turning text data into tokens"""

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

    def test_init_no_universe(self):
        """Attempt to configure with a configuration file without universe"""

        with self.assertLogs(level='WARNING'):
            result = CrossmapSettings(config_no_universe_file)
            self.assertTrue(result.valid)

    def test_full_paths(self):
        """Attempt to configure with a configuration file without universe"""

        result = CrossmapSettings(join(data_dir, "config.yaml"))
        self.assertEqual(len(result.files("universe")), 1)
        self.assertEqual(result.files("universe"), [dataset_file])
