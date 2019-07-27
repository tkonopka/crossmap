'''Tests for mapping across datasets using token similarities
'''

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.settings import CrossmapSettings
from crossmap.tools import read_dict
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_simple = join(data_dir, "config-simple.yaml")
config_nodocs = join(data_dir, "config-no-documents.yaml")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapInitTests(unittest.TestCase):
    """Special cases for initialization"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_init_from_settings(self):
        """Initializing a crossmap object create directory structure"""

        settings = CrossmapSettings(data_dir)
        subdir = settings.data_dir
        self.assertEqual(subdir, join(data_dir, "crossmap_simple"))
        # data directory does not exist before init, exists after
        self.assertFalse(exists(subdir))
        Crossmap(settings) #initializing using a settings object
        self.assertTrue(exists(subdir))

    def test_init_from_dir(self):
        """Initializing a crossmap object create directory structure"""

        subdir = join(data_dir, "crossmap_simple")
        # data directory does not exist before init, exists after
        self.assertFalse(exists(subdir))
        crossmap = Crossmap(data_dir) # initilizing using a plain directory
        self.assertTrue(exists(subdir))
        self.assertEqual(crossmap.settings.data_dir, subdir)


class CrossmapBuildStandardTests(unittest.TestCase):
    """Building a crossmap object"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        cls.crossmap = Crossmap(config_simple)
        cls.crossmap.build()
        cls.feature_map_file = cls.crossmap.settings.tsv_file("feature-map")

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_valid_status(self):
        """crossmap should report a valid status because settings are valid"""
        self.assertTrue(self.crossmap.valid())

    def test_feature_map_is_saved(self):
        """Build records a feature map"""

        fm_file = self.crossmap.settings.tsv_file("feature-map")
        self.assertTrue(exists(fm_file))
        features = read_dict(fm_file)
        self.assertTrue("with" in features)
        self.assertTrue("start" in features)
        self.assertTrue("that" in features)

    def test_indexes_are_saved(self):
        """Build records a feature map"""

        targets_file = self.crossmap.settings.index_file("targets")
        docs_file = self.crossmap.settings.index_file("documents")
        self.assertTrue(exists(targets_file))
        self.assertTrue(exists(docs_file))


class CrossmapBuildNoDocsTests(unittest.TestCase):
    """Building a crossmap object without documents"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_nodocs")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_nodocs")

    def test_target_index_is_saved(self):
        """Build without documents saves one index"""

        # build crossmap object and indexes
        with self.assertLogs(level='WARNING') as cm1:
            crossmap = Crossmap(config_nodocs)
        self.assertTrue("Configuration does not specify" in str(cm1.output))
        self.assertTrue("documents" in str(cm1.output))
        with self.assertLogs(level='WARNING') as cm2:
            crossmap.build()
        self.assertTrue("Skipping build" in str(cm2.output))
        self.assertTrue("for documents" in str(cm2.output))

        targets_file = crossmap.settings.index_file("targets")
        docs_file = crossmap.settings.index_file("documents")
        self.assertTrue(exists(targets_file))
        self.assertFalse(exists(docs_file))

