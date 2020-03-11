"""
Tests for obtaining feature co-occurance and diffusing vectors
"""

import unittest
from os.path import join
from crossmap.settings import CrossmapSettings
from crossmap.indexer import CrossmapIndexer
from crossmap.diffuser import CrossmapDiffuser
from crossmap.tokenizer import CrossmapTokenizer, CrossmapDiffusionTokenizer
from crossmap.diffuser import _pass_weights
from .tools import remove_crossmap_cache
from crossmap.vectors import sparse_to_dense
from crossmap.distance import euc_dist


data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
config_longword = join(data_dir, "config-longword.yaml")


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

    def test_diffuser_build_adds_count_rows(self):
        """count tables should have one row per feature"""

        n = len(self.feature_map)
        # there are two datasets (targets, documents), each with n rows
        self.assertEqual(self.db.count_rows("targets", "counts"), n)
        self.assertEqual(self.db.count_rows("documents", "counts"), n)

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
        """extract counts from db for multiple features"""

        fm = self.feature_map
        a, b = fm["a"][0], fm["b"][0]
        # db fetch should provide counts for one feature
        result = self.db.get_counts("targets", [a, b])
        self.assertEqual(len(result), 2)
        # count vector should match feature map length
        self.assertEqual(len(result[a].toarray()[0]), len(fm))
        self.assertEqual(len(result[b].toarray()[0]), len(fm))

    def test_retrieve_from_documents(self):
        """extract counts from documents"""

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


class CrossmapDiffuserBuildReBuildTests(unittest.TestCase):
    """Managing co-occurance counts"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        cls.indexer = CrossmapIndexer(settings)
        cls.indexer.build()
        cls.diffuser = CrossmapDiffuser(settings)
        cls.diffuser.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_rebuild_aborts(self):
        """attempting to rebuild should signal and abort"""

        diffuser = self.diffuser
        before = diffuser.db.count_rows("targets", "counts")
        self.assertGreater(before, 0)

        with self.assertLogs(level="WARNING") as cm:
            self.diffuser.build()
        self.assertTrue("exists" in str(cm.output))

        after = diffuser.db.count_rows("targets", "counts")
        self.assertEqual(after, before)


class CrossmapDiffuserWeightsTests(unittest.TestCase):
    """Checking overlapping tokens do not swamp diffusion"""

    long_b = dict(data="longword B")
    gh = dict(data="G H")

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_longword, create_dir=True)
        cls.indexer = CrossmapIndexer(settings)
        cls.indexer.build()
        cls.diffuser = CrossmapDiffuser(settings)
        cls.diffuser.build()
        cls.feature_map = cls.diffuser.feature_map
        cls.db = cls.diffuser.db
        cls.encoder = cls.indexer.encoder
        cls.plain_tokenizer = CrossmapTokenizer(settings)
        cls.diff_tokenizer = CrossmapDiffusionTokenizer(settings)
        # extract data vectors
        cls.data = dict()
        temp = cls.db.get_data(dataset="targets",
                                   ids=["L0", "L1", "L2", "L3", "L4"])
        for _ in temp:
            cls.data[_["id"]] = sparse_to_dense(_["data"])

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_longword")

    def test_diffusion_shifts_away_from_a_target(self):
        """example using diffusion unaffected by longword"""

        # before diffusion gh should be roughly equally distant to L3 and L4
        v = self.encoder.document(self.gh)
        v_dense = sparse_to_dense(v)
        self.assertAlmostEqual(euc_dist(v_dense, self.data["L3"]),
                               euc_dist(v_dense, self.data["L4"]))

        # after diffusion, L3 should be clearly preferred
        # the strengths of diffusion should not matter here
        # (any diffusion should break a tie in favor or L3)
        vd = self.diffuser.diffuse(v, dict(documents=1))
        vd_dense = sparse_to_dense(vd)
        self.assertLess(euc_dist(vd_dense, self.data["L3"]),
                        euc_dist(vd_dense, self.data["L4"]))

    def test_longword_document_before_diffusion(self):
        """encoding before diffusion accounts for overlapping tokens"""

        v = self.encoder.document(self.long_b)
        self.assertGreater(len(v.data), 4)
        # overlapping tokens from "longword" should be weighted lower than
        # tokens from "B" or "C" that are stand-alone
        v_dense = sparse_to_dense(v)
        fm = self.feature_map
        self.assertGreater(v_dense[fm["b"][0]], v_dense[fm["ngwor"][0]])
        # document should be closer to L0 than to L1
        d0 = euc_dist(v_dense, self.data["L0"])
        d1 = euc_dist(v_dense, self.data["L1"])
        self.assertLess(d0, d1)

    def test_diffusion_shifts_away_from_longword(self):
        """encoding is reasonable after diffusion"""

        v = self.encoder.document(self.long_b, self.plain_tokenizer)
        w = self.encoder.document(self.long_b, self.diff_tokenizer)
        v_dense = sparse_to_dense(v)
        # w_dense = sparse_to_dense(w)
        vd = self.diffuser.diffuse(v, dict(targets=5))
        vd_dense = sparse_to_dense(vd)
        vd2 = self.diffuser.diffuse(v, dict(targets=5), weight=w)
        vd2_dense = sparse_to_dense(vd2)
        # distances from doc to targets before and after diffusion
        before, after, after2 = dict(), dict(), dict()
        for id, target in self.data.items():
            before[id] = euc_dist(target, v_dense)
            after[id] = euc_dist(target, vd_dense)
            after2[id] = euc_dist(target, vd2_dense)
        
        # document should become closer to L1 than to L0
        # i.e. opposite relation compared to previous test
        d0 = euc_dist(vd2_dense, self.data["L0"])
        d1 = euc_dist(vd2_dense, self.data["L1"])
        self.assertLess(d1, d0)

    def test_diffusion_keeps_original_feature_strong(self):
        """diffusing from one feature should mantain that feature strong"""

        doc = dict(data="C")
        c_index = self.feature_map["c"][0]
        v = self.encoder.document(doc)
        # diffuse at different strengths
        # all should maintain feature "C" as the most important feature
        for w in [1, 2, 4, 8, 20]:
            result = self.diffuser.diffuse(v, dict(targets=w))
            result_dense = sparse_to_dense(result)
            result_C = result_dense[c_index]
            result_max = max(result_dense)
            self.assertEqual(result_max, result_C)


class CrossmapDiffuserMultistep(unittest.TestCase):
    """diffusion through multiple passes"""

    def test_multistep_weights_1(self):
        """weighting for a single-step diffusion"""
        result = _pass_weights(1)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 1.0)

    def test_multistep_weights_2(self):
        """weighting for a two-step diffusion"""
        result = _pass_weights(2)
        self.assertEqual(len(result), 2)
        self.assertAlmostEqual(result[0], 2/3)
        self.assertAlmostEqual(result[1], 1/3)

    def test_multistep_weights_3(self):
        """weighting for a three-step diffusion"""

        result = _pass_weights(3)
        self.assertEqual(len(result), 3)
        self.assertAlmostEqual(result[0], 6/11)
        self.assertAlmostEqual(result[1], 3/11)
        self.assertAlmostEqual(result[2], 2/11)

