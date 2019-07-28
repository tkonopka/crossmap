'''Tests for turning documents into indexes
'''

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
dataset_file = join(data_dir, "dataset.yaml")
# not features for feature map should be in lowercase!
test_features = ["alice", "bob", "catherine", "daniel", "starts", "unique",
                 "alpha", "bravo", "charlie", "delta", "echo",
                 "a", "b", "c", "d", "e"]


class CrossmapIndexerBuildTests(unittest.TestCase):
    """Creating nearest neighbor indexes from documents and text tokens"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.index_file = settings.index_file("index-0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_indexer_build(self):
        """build indexes from a simple configuration"""

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
        """prepared indexes from disk"""

        indexer = self.indexer
        self.assertFalse(exists(self.index_file))
        indexer.build()
        indexer.indexes = []
        indexer.item_names = []
        indexer.items = dict()
        indexer.load()
        self.assertEqual(len(indexer.indexes), 2)
        self.assertEqual(len(indexer.item_names), 2)
        self.assertGreater(len(indexer.items), 6)
        self.assertEqual(indexer.indexes[0].get_n_items(), 6)

    def test_indexer_build_rebuild(self):
        """run a build when indexes already exist"""

        self.assertFalse(exists(self.index_file))
        self.indexer.build()
        # the second indexer is created from scratch, with the same settings
        # build should detect presence of indexes and load instead
        newindexer = CrossmapIndexer(self.indexer.settings,
                                     self.indexer.feature_map)
        with self.assertLogs(level="WARNING") as cm:
            newindexer.build()
        self.assertTrue("Skip" in str(cm.output))
        self.assertTrue("exists" in str(cm.output))
        # after build, the indexer should be ready to use
        items = newindexer.items
        self.assertGreater(len(items), 6,
                           "dataset has six items, documents have more items")
        self.assertEqual(len(newindexer.index_files), 2,
                         "one index for targets, one for documents")
        self.assertTrue(exists(newindexer.index_files[0]))
        self.assertTrue(exists(newindexer.index_files[1]))


class CrossmapIndexerNeighborTests(unittest.TestCase):
    """Mapping vectors into targets using nearest neighbors indexes"""

    @classmethod
    def setUpClass(self):
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.indexer.build()

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

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
        """find nearest neighbors among targets, A"""

        # this doc should be close to A and D
        doc = {"data": "Alice A and Daniel"}
        doc_vector = self.indexer.encode(doc)
        nns, distances = self.indexer.nearest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "D")

    def test_nn_targets_B(self):
        """find nearest neighbors among targets, B"""

        # this doc should be close to B, A, U
        doc = {"data": "Bob Bob Alice", "aux_pos": "unique"}
        doc_vector = self.indexer.encode(doc)
        nns, distances = self.indexer.nearest_targets(doc_vector, 3)
        self.assertEqual(nns[0], "B")
        self.assertEqual(nns[1], "A")
        self.assertEqual(nns[2], "U")

    def test_nn_documents_A(self):
        """find nearest neighbors among documents, A"""

        # this doc should be close to A and D
        doc = {"data": "Alpha A Delta D E"}
        doc_vector = self.indexer.encode(doc)
        nns, distances = self.indexer.nearest_documents(doc_vector, 2)
        self.assertEqual(nns[0], "U:D")
        self.assertEqual(nns[1], "U:A")

    def test_suggest_A(self):
        """target suggestion, direct hits possible"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A B", "aux_neg": "unique token"}
        doc_vector = self.indexer.encode(doc)
        nns, distances = self.indexer.suggest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")

    def test_suggest_alpha(self):
        """target suggestion, when direct hits not possible"""

        # this doc should be close to two auxiliary items
        doc = {"data": "alpha", "aux_pos": "bravo"}
        doc_vector = self.indexer.encode(doc)
        nns, distances = self.indexer.suggest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")
