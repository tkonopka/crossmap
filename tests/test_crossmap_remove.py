"""
Tests for removing datasets and whole instances
"""

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.dbmongo import InvalidDatasetLabel
from crossmap.settings import CrossmapSettings
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_single = join(data_dir, "config-single.yaml")


class CrossmapRemoveDatasetTests(unittest.TestCase):
    """Tests for removing individual datasets from a crossmap instance"""

    def setUp(self):
        settings = CrossmapSettings(config_single, create_dir=True)
        self.crossmap = Crossmap(settings)
        self.crossmap.build()
        self.assertTrue(self.crossmap)

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_single")

    def test_remove_dataset(self):
        """Initializing a crossmap object create directory structure"""

        crossmap = self.crossmap
        self.assertTrue(exists(crossmap.settings.prefix))
        new_doc = dict(data="A B C D")
        # dataset 'abc' does not exist, so searching should raise exception
        with self.assertRaises(Exception):
            crossmap.search(new_doc, "abc", n=1)
        crossmap.add("abc", new_doc, "abc:1")
        result_before = crossmap.search(new_doc, "abc", n=1)
        self.assertEqual(len(result_before["distances"]), 1)
        # removing dataset 'abc' should make search in 'abc' impossible
        crossmap.remove("abc")
        with self.assertRaises(InvalidDatasetLabel):
            crossmap.search(new_doc, "abc", n=1)
        # but most instances files and db should still exist
        result_targets = crossmap.search(new_doc, "targets", n=1)
        self.assertEqual(len(result_targets["distances"]), 1)
        self.assertTrue(exists(crossmap.settings.prefix))

    def test_remove_all_datasets(self):
        """remove all datasets from an instance"""

        crossmap = self.crossmap
        self.assertTrue(exists(crossmap.settings.prefix))
        doc = dict(data="A B")
        result_before = crossmap.search(doc, "targets", n=1)
        self.assertEqual(len(result_before["distances"]), 1)
        # removing the last document should prevent search ...
        crossmap.remove("targets")
        with self.assertRaises(InvalidDatasetLabel):
            crossmap.search(doc, "targets", n=1)
        # but some files and dir structure should still exist
        self.assertTrue(exists(crossmap.settings.prefix))

