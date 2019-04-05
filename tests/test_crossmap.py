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

include_file = join(data_dir, "test_include.txt")
exclude_file = join(data_dir, "test_exclude.txt")
exclude_file2 = join(data_dir, "test_exclude_2.txt")
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
        toks_file = join(data_dir, "crossmap0-target-tokens.txt")
        self.assertFalse(exists(toks_file))
        # first iteration should create the cache file
        result1 = crossmap.target_tokens()
        self.assertTrue(exists(toks_file))
        self.assertTrue("with" in result1)
        self.assertTrue("start" in result1)
        self.assertTrue("that" in result1)
        # second iteration should fetch from the cache
        result2 = crossmap.target_tokens()
        self.assertEqual(result1, result2)
        # both results should have all tokens
        self.assertTrue("complete" in result1)
        self.assertTrue("complete" in result2)

    def test_target_tokens_unique(self):
        """Target tokens should be unique"""

        crossmap = Crossmap(config_plain)
        result = crossmap.target_tokens()
        # output should be a set (i.e. unique strings)
        self.assertTrue(type(result) is set)

        # check content on disk is also composed of unique strings
        toks_file = join(data_dir, "crossmap0-target-tokens.txt")
        with open(toks_file, "rt") as f:
            tokens = f.readlines()
        self.assertEqual(len(tokens), len(result))

    def test_target_tokens_exclude(self):
        """Target tokens can exclude certain elements"""

        crossmap = Crossmap(config_exclude)
        result = crossmap.target_tokens()
        self.assertFalse("that" in result)
