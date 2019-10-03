"""
Tests for obtaining feature co-occurance and diffusing vectors
"""

import unittest
from os.path import join
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from crossmap.diffuser import CrossmapDiffuser
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")


class CrossmapDiffuserBuildTests(unittest.TestCase):
    """Managing co-occurance counts"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        cls.indexer = CrossmapIndexer(settings)
        cls.indexer.build()
        cls.diffuser = CrossmapDiffuser(settings)
        cls.diffuser.build()
        cls.feature_map = cls.diffuser.feature_map
        cls.db = cls.diffuser.db
        cls.encoder = cls.indexer.encoder

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_diffuser_db_structure(self):
        """features in db and feature map should match"""
        db_features = self.db._count_rows("features")
        self.assertEqual(len(self.feature_map), db_features)

    def test_diffuser_build_adds_count_rows(self):
        """count tables should have one row per feature"""

        n = len(self.feature_map)
        # there are two datasets (targets, documents), so 2n rows
        self.assertEqual(self.db._count_rows("counts"), 2*n)

    def test_retrieve_counts(self):
        """extract counts from db for one feature"""

        fm = self.feature_map
        alice_idx = fm["alice"][0]
        # db fetch should provide counts for one feature
        result = self.db.get_counts("targets", [alice_idx])
        self.assertEqual(len(result), 1)
        # count vector should match feature map length
        data = result[alice_idx].toarray()[0]
        self.assertEqual(len(data), len(fm))
        # count vector should have nonzero counts for co-occuring features
        start_idx = fm["start"][0]
        with_idx = fm["with"][0]
        self.assertGreater(data[start_idx], 0)
        self.assertGreater(data[with_idx], 0)
        # count vector should not have counts for non-co-occurring features
        abcde_idx = fm["abcde"][0]
        self.assertEqual(data[abcde_idx], 0)

    def test_retrieve_many_counts(self):
        """extract counts from db for multiple feature"""

        fm = self.feature_map
        a, b = fm["a"][0], fm["b"][0]
        # db fetch should provide counts for one feature
        result = self.db.get_counts("targets", [a, b])
        self.assertEqual(len(result), 2)
        # count vector should match feature map length
        self.assertEqual(len(result[a].toarray()[0]), len(fm))
        self.assertEqual(len(result[b].toarray()[0]), len(fm))

    def test_retrieve_from_documents(self):
        """extract counts from db for multiple feature"""

        fm = self.feature_map
        a = fm["a"][0]
        # db fetch should provide counts for one feature
        result_targets = self.db.get_counts("targets", [a])
        result_docs = self.db.get_counts("documents", [a])
        self.assertEqual(len(result_targets), 1)
        self.assertEqual(len(result_docs), 1)
        counts_targets = result_targets[a].toarray()[0]
        counts_docs = result_docs[a].toarray()[0]
        # the letter a appears more often in documents than in targets
        self.assertGreater(counts_docs[a], counts_targets[a])
        # the letter co-occurs with 'alpha' in documents
        alpha = fm["alpha"][0]
        self.assertGreater(counts_docs[alpha], counts_targets[alpha])

    def test_diffuse_vector(self):
        """diffuse a vector values, basic properties"""

        doc = {"data": "alice"}
        doc_data = self.encoder.document(doc)
        strength = dict(targets=1, documents=1)
        result = self.diffuser.diffuse(doc_data, strength)
        result_array = result.toarray()[0]
        # raw data has only one feature
        self.assertEqual(len(doc_data.indices), 1)
        # diffused data should have several
        self.assertGreater(len(result.indices), 2)
        result_indices = list(result.indices)
        alice_idx = self.feature_map["alice"][0]
        with_idx = self.feature_map["with"][0]
        a_idx = self.feature_map["a"][0]
        self.assertTrue(with_idx in result_indices)
        self.assertTrue(a_idx in result_indices)
        # diffused values should be lower than the primary item
        self.assertLess(result_array[with_idx], result_array[alice_idx])
        self.assertLess(result_array[a_idx], result_array[alice_idx])

    def test_diffuse_vector_custom_weights(self):
        """diffuse a vector with custom weights"""

        doc = {"data": "alice"}
        doc_data = self.encoder.document(doc)
        strength_weak = dict(targets=1, documents=1)
        result1 = self.diffuser.diffuse(doc_data, strength_weak)
        array1 = result1.toarray()[0]
        strength_strong = dict(targets=10, documents=10)
        result2 = self.diffuser.diffuse(doc_data, strength_strong)
        array2 = result2.toarray()[0]
        # second result uses more aggressive diffusion,
        # diffused values should be larger
        with_idx = self.feature_map["with"][0]
        self.assertEqual(doc_data.toarray()[0][with_idx], 0.0)
        self.assertGreater(array2[with_idx], array1[with_idx])

