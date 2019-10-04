"""
Tests for adding documents into a new dataset
"""

import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.tools import yaml_document
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file= join(data_dir, "config-simple.yaml")


@unittest.skip
class CrossmapAddTests(unittest.TestCase):
    """Adding single documents into a dataset"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        cls.db = cls.crossmap.indexer.db
        cls.manual_file = cls.crossmap.settings.yaml_file("manual")
        # at start, project only has "targets" and "documents" datasets
        cls.assertFalse(exists(cls.manual_file))
        cls.assertEqual(len(cls.crossmap.indexer.db.datasets), 2)

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_add_to_targets(self):
        """cannot add new data to file-derived datasets"""

        doc = dict(data="Alice and Bob", aux_pos="Alpha and Bravo")
        size_before = self.crossmap.indexer.db._count_rows("data", "targets")
        # attempt to add to dataset
        with self.assertRaises(Exception) as cm:
            self.crossmap.add(doc, "targets", id="T0")
        self.expectTrue("targets" in str(cm.output))
        # attempt should do nothing, i.e. outcome None, db unchanged
        size_after = self.crossmap.indexer.db._count_rows("data", "targets")
        self.assertEqual(size_before, size_after)

    def test_add_disk_file(self):
        """adding new object should create a disk file"""

        doc = {"data": "alpha bravo charlie"}
        self.crossmap.add(doc, "manual", id="Tdisk")
        self.assertTrue(exists(self.manual_file))
        # content of disk file should contain document
        disk_docs = dict()
        with open(self.manual_file, "rt") as f:
            for id, doc in yaml_document(f):
                disk_docs[id] = doc
        self.assertTrue("Tdisk" in disk_docs)
        self.assertTrue("charlie" in disk_docs["data"])

    def test_add_simple_item(self):
        """add new object into data table"""

        doc = dict(data="Alice and Bob", aux_pos="Alpha and Bravo")
        result = self.crossmap.add(doc, "manual", id="T0")
        # attempt should provide a not-None response
        self.assertNotEqual(result, None)
        self.assertGreater(result, -1)
        # the new record should exist in the database
        db = self.crossmap.indexer.db
        self.assertTrue("manual" in db.datasets)
        self.assertGreater(db._count_rows("data", "manual"), 0)
        # db should contain a data record with features from the doc
        doc_data = db.get_data("manual", ids=["T0"])[0]
        print(str(doc_data))
        fm = self.crossmap.indexer.feature_map
        alice_idx = fm["alice"][0]
        self.assertEqual(doc_data["data"].shape[1], len(fm))
        self.assertGreater(doc_data["data"][0, alice_idx], 0)

    def test_add_repeat_id(self):
        """cannot add two elements with same id"""

        doc1 = dict(data="new data item")
        # adding this document should be accepted
        result = self.crossmap.add(doc1, "manual", id="T1")
        self.assertNotEqual(result, None)
        self.assertGreater(result, -1)
        size_before = self.db._count_rows("data", "manual")
        # a second attempt to add a doc with same id should not work
        doc2 = {"data": "Another data item"}
        with self.assertRaises(Exception) as cm:
            self.crossmap.add(doc2, "manual", id="T1")
        size_after = self.db._count_rows("data", "manual")
        self.assertEqual(size_before, new_count)

