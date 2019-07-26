'''Tests for turning documents into indexes
'''

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "crossmap.yaml")
dataset_file = join(data_dir, "dataset.yaml")
test_features = ["alice", "bob", "catherine", "daniel", "starts", "unique"]


class CrossmapIndexerBuildTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        settings = CrossmapSettings(config_plain)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.index_file = settings.index_file("index-0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_indexer_build(self):
        """extract tokens with empty documents list"""

        self.assertFalse(exists(self.index_file))
        self.indexer.build()
        items = self.indexer.items
        self.assertGreater(len(items), 6,
                           "dataset has six items, documents have more items")
        self.assertEqual(len(self.indexer.index_files), 2,
                         "one index for targets, one for documents")
        self.assertTrue(exists(self.indexer.index_files[0]))
        self.assertTrue(exists(self.indexer.index_files[1]))

    def test_indexer_load(self):
        """extract tokens with empty documents list"""

        indexer = self.indexer
        self.assertFalse(exists(self.index_file))
        indexer.build()
        indexer.indexes = []
        indexer.load()
        self.assertEqual(len(indexer.indexes), 2)
        self.assertEqual(indexer.indexes[0].get_n_items(), 6)


class CrossmapIndexerNeighborTests(unittest.TestCase):
    """Turning text data into tokens"""

    @classmethod
    def setUpClass(self):
        settings = CrossmapSettings(config_plain)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.indexer.build()

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_setup(self):
        """class should set up correctly with two indexes"""

        self.assertEqual(len(self.indexer.indexes), 2)
        self.assertEqual(len(self.indexer.item_names), 2)
        self.assertEqual(len(self.indexer.index_files), 2)
        index_targets = self.indexer.indexes[0]
        index_docs = self.indexer.indexes[1]
        self.assertEqual(index_targets.get_n_items(), 6,
                         "dataset has six items")
        self.assertGreater(index_docs.get_n_items(), 10,
                           "dataset has many items")

    def test_nn_targets_A(self):
        """extract tokens with empty documents list"""

        item_names = self.indexer.item_names[0]
        # this doc should be close to A and D
        doc = {"data": "Alice A and Daniel"}
        nn, distances = self.indexer._neighbors(doc, 2)
        self.assertEqual(item_names[nn[0]], "A")
        self.assertEqual(item_names[nn[1]], "D")

    def test_nn_targets_B(self):
        """extract tokens with empty documents list"""

        item_names = self.indexer.item_names[0]
        # this doc should be close to B, A, U
        doc = {"data": "Bob Bob Alice", "aux_pos": "unique"}
        nn, distances = self.indexer._neighbors(doc, 3)
        self.assertEqual(item_names[nn[0]], "B")
        self.assertEqual(item_names[nn[1]], "A")
        self.assertEqual(item_names[nn[2]], "U")

