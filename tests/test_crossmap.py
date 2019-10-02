"""
Tests for mapping across datasets using token similarities
"""

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.settings import CrossmapSettings
from crossmap.tools import read_dict
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_simple = join(data_dir, "config-simple.yaml")
config_noname = join(data_dir, "config-no-name.yaml")
config_nodocs = join(data_dir, "config-single.yaml")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapInitTests(unittest.TestCase):
    """Special cases for initialization"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_default")

    def test_init_from_settings(self):
        """Initializing a crossmap object create directory structure"""

        # create settings by providing a directory
        # This will trigger search for crossmap.yaml
        settings = CrossmapSettings(data_dir)
        subdir = settings.prefix
        self.assertEqual(subdir, join(data_dir, "crossmap_default"))
        # data directory does not exist before init, exists after
        self.assertFalse(exists(subdir))
        # initializing using a settings object
        crossmap = Crossmap(settings)
        self.assertTrue(exists(subdir))
        # the crossmap is not valid because it has not been build yet
        self.assertFalse(crossmap.valid)

    def test_init_from_invalid(self):
        """Initializing with an invalid configuration file"""

        with self.assertLogs(level="ERROR") as cm:
            crossmap = Crossmap(config_noname)
        self.assertTrue("name" in str(cm.output))
        self.assertFalse(crossmap.valid)


class CrossmapBuildEmptyTests(unittest.TestCase):
    """Special cases for initialization - empty datasets"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_empty_documents")
        remove_crossmap_cache(data_dir, "crossmap_empty")

    def test_init_empty_targets_no_documents(self):
        """targets data file cannot be empty"""

        with self.assertLogs(level="ERROR") as cm:
            crossmap = Crossmap(join(data_dir, "config-empty.yaml"))
            crossmap.build()
        self.assertTrue("data" in str(cm.output))
        self.assertFalse(crossmap.valid)

    def test_init_empty_documents(self):
        """Initializing with an empty dataset file"""

        with self.assertLogs(level="WARNING") as cm:
            crossmap = Crossmap(join(data_dir, "config-empty-documents.yaml"))
            crossmap.build()
        self.assertTrue("No content" in str(cm.output))
        self.assertTrue("documents" in str(cm.output))
        self.assertTrue(crossmap.valid)


class CrossmapBuildStandardTests(unittest.TestCase):
    """Building a crossmap object"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_simple)
        cls.crossmap.build()
        cls.feature_map_file = cls.crossmap.settings.tsv_file("feature-map")

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_valid_status(self):
        """crossmap should report a valid status because settings are valid"""

        self.assertTrue(self.crossmap.valid)

    def test_default_dataset_label(self):
        """the build process should set a default dataset label"""

        self.assertEqual(self.crossmap.default_label, "targets")

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

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_single")

    def test_target_index_is_saved(self):
        """Build without documents saves one index"""

        crossmap = Crossmap(config_nodocs)
        crossmap.build()

        targets_file = crossmap.settings.index_file("targets")
        docs_file = crossmap.settings.index_file("documents")
        self.assertTrue(exists(targets_file))
        self.assertFalse(exists(docs_file))

