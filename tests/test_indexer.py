'''Tests for turning documents into indexes
'''

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
config_nodocs = join(data_dir, "config-no-documents.yaml")
dataset_file = join(data_dir, "dataset.yaml")
# not features for feature map should be in lowercase!
test_features = ["alice", "bob", "catherine", "daniel", "starts", "unique", "file",
                 "alpha", "bravo", "charlie", "delta", "echo",
                 "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]


class CrossmapIndexerBuildTests(unittest.TestCase):
    """Creating nearest neighbor indexes from documents and text tokens"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.index_file = settings.annoy_file("index-0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_indexer_build(self):
        """build indexes from a simple configuration"""

        self.assertFalse(exists(self.index_file))
        self.indexer.build()
        num_targets = self.indexer.db._count_rows(table="targets")
        num_docs = self.indexer.db._count_rows(table="documents")
        self.assertEqual(num_targets, 6, "dataset has six items")
        self.assertGreater(num_docs, 6, "documents have several items")
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
        indexer.load()
        self.assertEqual(len(indexer.indexes), 2)
        # both index and data db should record items
        self.assertEqual(indexer.db._count_rows("targets"), 6)
        self.assertGreater(indexer.db._count_rows("documents"), 6)

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
        num_targets = newindexer.db._count_rows(table="targets")
        num_docs = newindexer.db._count_rows(table="documents")
        self.assertEqual(num_targets, 6, "dataset still has six items")
        self.assertGreater(num_docs, 6, "targets have many items")
        self.assertTrue(exists(newindexer.index_files[0]))
        self.assertTrue(exists(newindexer.index_files[1]))


class CrossmapIndexerSkippingTests(unittest.TestCase):
    """Building indexing and skipping over items that have null features vectors"""

    limited_features = ["alice", "bob", "catherine", "daniel", "starts", "unique", "file",
                        "a", "b", "c", "d", "e"]

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_skip_certain_docs(self):
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        indexer = CrossmapIndexer(settings, self.limited_features)
        with self.assertLogs(level="WARNING") as cm:
            indexer.build()
        self.assertTrue("null" in str(cm.output))


class CrossmapIndexerNeighborTests(unittest.TestCase):
    """Mapping vectors into targets using nearest neighbors indexes"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        cls.indexer = CrossmapIndexer(settings, test_features)
        cls.feature_map = cls.indexer.feature_map
        cls.indexer.build()

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_setup(self):
        """class should set up correctly with two indexes"""

        self.assertEqual(len(self.indexer.indexes), 2)
        self.assertEqual(len(self.indexer.index_files), 2)

    def test_nn_targets_A(self):
        """find nearest neighbors among targets, A"""

        # this doc should be close to A and D
        doc = {"data": "Alice A and Daniel"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "D")

    def test_nn_targets_B(self):
        """find nearest neighbors among targets, B"""

        # this doc should be close to B, A, U
        doc = {"data": "Bob Bob Alice", "aux_pos": "Alice unique"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest_targets(doc_vector, 3)
        self.assertEqual(nns[0], "B")
        self.assertEqual(nns[1], "A")
        self.assertEqual(nns[2], "U")

    def test_nn_documents_A(self):
        """find nearest neighbors among documents, A"""

        # this doc should be close to A and D
        doc = {"data": "Alpha A Delta D E"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest_documents(doc_vector, 2)
        self.assertEqual(nns[0], "U:D")
        self.assertEqual(nns[1], "U:A")

    def test_suggest_A(self):
        """target suggestion, direct hits possible"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A B", "aux_neg": "unique token"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.suggest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")

    def test_suggest_alpha(self):
        """target suggestion, when direct hits not possible"""

        # this doc should be close to two auxiliary items
        doc = {"data": "alpha", "aux_pos": "A bravo"}
        doc_vector = self.indexer.encode_document(doc)
        temp = self.indexer.db.get_targets(idxs=[4])
        nns, distances = self.indexer.suggest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")


class CrossmapIndexerNeighborNoDocsTests(unittest.TestCase):
    """Mapping vectors into targets when document index is missing"""

    @classmethod
    def setUpClass(cls):
        """build an indexer using target documents only"""

        # this construction "with" avoid displaying warning messages
        # during the test procedure
        with cls.assertLogs(cls, level="WARNING") as cm:
            settings = CrossmapSettings(config_nodocs, create_dir=True)
            settings.tokens.k = 10
            cls.indexer = CrossmapIndexer(settings, test_features)
            cls.feature_map = cls.indexer.feature_map
            cls.indexer.build()
        cls.assertTrue(cls, "documents" in str(cm.output))
        cls.assertTrue(cls, "no data" in str(cm.output))

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_nodocs")

    def test_setup(self):
        """class should set up correctly with two indexes"""

        self.assertEqual(len(self.indexer.indexes), 2)
        self.assertEqual(len(self.indexer.index_files), 2)
        # second index should not exist
        self.assertEqual(self.indexer.index_files[1], None)
        self.assertEqual(self.indexer.indexes[1], None)

    def test_suggest_nodocs_A(self):
        """target suggestion"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A Bob"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.suggest_targets(doc_vector, 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")
