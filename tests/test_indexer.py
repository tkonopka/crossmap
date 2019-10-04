"""
Tests for turning documents into indexes
"""

import unittest
from os.path import join, exists
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
config_single = join(data_dir, "config-single.yaml")
config_featuremap = join(data_dir, "config-featuremap.yaml")
dataset_file = join(data_dir, "dataset.yaml")
# not features for feature map should be in lowercase!
test_features = ["alice", "bob", "catherine", "daniel", "starts", "unique", "file",
                 "alpha", "bravo", "charlie", "delta", "echo",
                 "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]


class CrossmapIndexerBuildTests(unittest.TestCase):
    """Creating nearest neighbor indexes from documents and text tokens"""

    def setUp(self):
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        self.indexer = CrossmapIndexer(settings, test_features)
        self.feature_map = self.indexer.feature_map
        self.index_file = settings.index_file("targets")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_indexer_build(self):
        """build indexes from a simple configuration"""

        self.assertFalse(exists(self.index_file))
        self.indexer.build()
        ids_targets = self.indexer.db.all_ids("targets")
        ids_docs = self.indexer.db.all_ids("documents")
        self.assertEqual(len(ids_targets), 6, "dataset has six items")
        self.assertGreater(len(ids_docs), 6, "documents have several items")
        self.assertEqual(len(self.indexer.index_files), 2,
                         "one index for targets, one for documents")
        self.assertTrue(exists(self.indexer.index_files["targets"]))
        self.assertTrue(exists(self.indexer.index_files["documents"]))

    def test_indexer_load(self):
        """prepared indexes from disk"""

        indexer = self.indexer
        self.assertFalse(exists(self.index_file))
        indexer.build()
        indexer.indexes = []
        indexer.load()
        self.assertEqual(len(indexer.indexes), 2)
        # both index and data db should record items
        self.assertEqual(len(indexer.db.all_ids("targets")), 6)
        self.assertGreater(len(indexer.db.all_ids("documents")), 6)

    def test_indexer_build_rebuild(self):
        """run a build when indexes already exist"""

        self.assertFalse(exists(self.index_file))
        self.indexer.build()
        # the second indexer is created from scratch, with the same settings
        # build should detect presence of indexes and load instead
        with self.assertLogs(level="WARNING") as cm:
            newindexer = CrossmapIndexer(self.indexer.settings,
                                         self.indexer.feature_map)
            newindexer.build()
        self.assertTrue("Skip" in str(cm.output))
        # after build, the indexer should be ready to use
        ids_targets = newindexer.db.all_ids("targets")
        ids_docs = newindexer.db.all_ids("documents")
        self.assertEqual(len(ids_targets), 6, "dataset still has six items")
        self.assertGreater(len(ids_docs), 6, "targets have many items")
        self.assertTrue(exists(newindexer.index_files["targets"]))
        self.assertTrue(exists(newindexer.index_files["documents"]))

    def test_indexer_str(self):
        """str summarizes main properties"""

        self.assertTrue("Indexes:\t0" in str(self.indexer))
        self.indexer.build()
        self.assertTrue("Indexes:\t2" in str(self.indexer))


class CrossmapIndexerSkippingTests(unittest.TestCase):
    """Building indexing and skipping over items that have null features vectors"""

    limited_features = ["alice", "bob", "catherine", "daniel", "starts", "unique", "file",
                        "a", "b", "c", "d", "e"]

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_skip_certain_docs(self):
        settings = CrossmapSettings(config_plain, create_dir=True)
        settings.tokens.k = 10
        indexer = CrossmapIndexer(settings, self.limited_features)
        with self.assertLogs(level="WARNING") as cm:
            indexer.build()
        self.assertTrue("item id" in str(cm.output))


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
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_setup(self):
        """class should set up correctly with two indexes"""

        self.assertEqual(len(self.indexer.indexes), 2)
        self.assertEqual(len(self.indexer.index_files), 2)

    def test_nn_targets_A(self):
        """find nearest neighbors among targets, A"""

        # this doc should be close to A and D
        doc = {"data": "Alice A and Daniel"}
        v = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest(v, "targets", 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "D")

    def test_nn_targets_B(self):
        """find nearest neighbors among targets, B"""

        # this doc should be close to B, A, U
        doc = {"data": "Bob Bob Alice", "aux_pos": "Alice unique"}
        v = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest(v, "targets", 3)
        self.assertEqual(nns[0], "B")
        self.assertEqual(nns[1], "A")
        self.assertEqual(nns[2], "U")

    def test_nn_documents_A(self):
        """find nearest neighbors among documents, A"""

        # this doc should be close to A and D
        doc = {"data": "Alpha A Delta D E"}
        v = self.indexer.encode_document(doc)
        nns, distances = self.indexer.nearest(v, "documents", 2)
        self.assertEqual(nns[0], "U:D")
        self.assertEqual(nns[1], "U:A")

    def test_suggest_A_wo_docs(self):
        """target suggestion, direct hits possible"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A B", "aux_neg": "unique token"}
        v = self.indexer.encode_document(doc)
        nns, distances = self.indexer.suggest(v, "targets", 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")

    def test_suggest_A_w_docs(self):
        """target suggestion, direct hits possible, using aux docs"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A B", "aux_neg": "unique token"}
        v = self.indexer.encode_document(doc)
        aux = dict(documents=2)
        nns, distances = self.indexer.suggest(v, "targets", 2, aux)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")

    def test_suggest_alpha(self):
        """target suggestion, when direct hits not possible"""

        # this doc should be close to two auxiliary items
        doc = {"data": "alpha", "aux_pos": "A bravo"}
        v = self.indexer.encode_document(doc)
        aux = dict(documents=2)
        nns, distances = self.indexer.suggest(v, "targets", 2, aux)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")
        # the distances should not be equal
        self.assertNotEqual(distances[0], distances[1])

    def test_suggest_without_docs(self):
        """make target suggestion without docs"""

        # this doc should be close to two auxiliary items
        # but no overlap with target items
        doc = {"data": "alpha", "aux_pos": "bravo"}
        v = self.indexer.encode_document(doc)
        aux = dict(documents=0)
        nns, distances = self.indexer.suggest(v, "targets", 2, aux)
        # without any help from the documents,
        # all distances to targets should be equal
        self.assertEqual(distances[0], distances[1])

    def test_suggest_many_docs(self):
        """make target suggestiosn and ask for more docs than available"""

        # this doc should be close to two auxiliary items
        # but no overlap with target items
        doc = {"data": "alpha", "aux_pos": "bravo"}
        v = self.indexer.encode_document(doc)
        aux = dict(documents=100)
        nns, distances = self.indexer.suggest(v, "targets", 2, aux)
        # the objective here is for the calculation not to crash
        self.assertLess(distances[0], distances[1])


class CrossmapIndexerNeighborNoDocsTests(unittest.TestCase):
    """Mapping vectors into targets when document index is missing"""

    @classmethod
    def setUpClass(cls):
        """build an indexer using target documents only"""

        settings = CrossmapSettings(config_single, create_dir=True)
        settings.tokens.k = 10
        cls.indexer = CrossmapIndexer(settings, test_features)
        cls.feature_map = cls.indexer.feature_map
        cls.indexer.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_single")

    def test_setup(self):
        """class should set up correctly with two indexes"""

        self.assertEqual(len(self.indexer.indexes), 1)
        self.assertEqual(len(self.indexer.index_files), 1)

    def test_suggest_nodocs_A(self):
        """target suggestion"""

        # this doc should be close to first two items in target dataset
        doc = {"data": "Alice", "aux_pos": "A Bob"}
        doc_vector = self.indexer.encode_document(doc)
        nns, distances = self.indexer.suggest(doc_vector, "targets", 2)
        self.assertEqual(nns[0], "A")
        self.assertEqual(nns[1], "B")


class CrossmapIndexerFixedFeaturemapTests(unittest.TestCase):
    """An indexer using a file-based featuremap"""

    @classmethod
    def setUpClass(cls):
        """build an indexer using a fixed featuremap"""

        settings = CrossmapSettings(config_featuremap, create_dir=True)
        settings.tokens.k = 20
        cls.indexer = CrossmapIndexer(settings)
        cls.indexer.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_featuremap")

    def test_loads_features_from_file(self):
        """features should match exactly content of file"""

        featuremap = self.indexer.feature_map
        # file has a limited number or tokens (alpha, beta, ..., echo)
        self.assertEqual(len(featuremap), 8)
        self.assertTrue("alpha" in featuremap)
        self.assertTrue("echo" in featuremap)
        self.assertTrue("entry" in featuremap)
        self.assertFalse("alice" in featuremap)

    def test_feature_weights_from_file(self):
        """weights in file are not all equal to 1.0"""

        featuremap = self.indexer.feature_map
        self.assertEqual(featuremap["alpha"][1], 1.0)
        self.assertNotEqual(featuremap["beta"][1], 1.0)

    def test_transfers_features_into_db(self):
        """after creating indexes, features are stored in db"""

        featuremap = self.indexer.feature_map
        dbmap = self.indexer.db.get_feature_map()
        self.assertEqual(len(featuremap), len(dbmap))

    def test_saves_features_file(self):
        """after creating indexes, copies features into project directory"""

        feature_file = self.indexer.settings.tsv_file("feature-map")
        self.assertTrue(exists(feature_file))

