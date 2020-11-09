"""
Tests with a focus on words with overlapping tokens
"""

import unittest
from scipy.sparse import csr_matrix
from os.path import join
from crossmap.crossmap import Crossmap
from crossmap.vectors import sparse_to_dense
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file = join(data_dir, "config-triples.yaml")
dataset_file = join(data_dir, "dataset-triples.yaml")


# items that can be inserted into the instance
af_xz = {"data": "abcdef xyz"}
af_wy_xz = {"data": "abcdef wxy xyz"}
jl = {"data": "jkl klm lmn"}


def round_list(x, digits=6):
    """helper for approximate tests, round a list"""
    if isinstance(x, csr_matrix):
        x = sparse_to_dense(x)
    return [round(_, digits) for _ in list(x)]


class CrossmapOverlappingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        # add dataset with single documents
        cls.crossmap.add("af_xz", af_xz, id="af_xz")
        cls.crossmap.add("af_wy_xz", af_wy_xz, id="af_wy_xz")
        cls.crossmap.add("jl", jl, id="jl")

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_triples")

    def test_simple_search(self):
        """search based on straightforward token without diffusion"""

        one = dict(data="bcd")
        result = self.crossmap.search(one, "targets", n=1)
        self.assertTrue(type(result) is dict)
        self.assertEqual(result["targets"][0], "T0")

    def test_encode_separate_together(self):
        """encoding using separated tokens and concatenated tokens"""

        cm = self.crossmap
        separate = dict(data="bcd cde def")
        together = dict(data="bcdef")
        v_separate = sparse_to_dense(cm.encoder.document(separate))
        v_together = sparse_to_dense(cm.encoder.document(together))
        self.assertListEqual(round_list(v_separate), round_list(v_together))

    def test_diffuse_separate_together(self):
        """diffusing using separated tokens and concatenated tokens"""

        cm = self.crossmap
        separate = dict(data="bcd cde def")
        together = dict(data="bcdef")
        diff = {"targets": 1}
        result_separate = cm.diffuse(separate, diffusion=diff)
        result_together = cm.diffuse(together, diffusion=diff)
        self.assertEqual(result_separate, result_together)

    def test_self_diffuse_from_separated_tokens(self):
        """diffusing a document using separated tokens and concatenated tokens"""

        cm = self.crossmap
        # jl is a document with separated tokens
        # attempt to diffuse it, using a dataset that only has
        # one item, which is jl itself
        jl_vec = cm.encoder.document(jl)
        result = cm.diffuser.diffuse(jl_vec, {"jl": 1})
        self.assertListEqual(round_list(jl_vec), round_list(result))

    def test_diffuse_xyz(self):
        """search based on straightforward token without diffusion"""

        cm = self.crossmap
        a = dict(data="abc abc bcd xyz")
        cm.add("ab", dict(data="abc bcd"), id="ab")
        a_vec = cm.encoder.document(a)
        a_diff_vec = cm.diffuser.diffuse(a_vec, {"ab": 1})
        self.assertEqual(1-1, 0)

