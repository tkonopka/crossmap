'''Tests for turning documents into tokens
'''

import unittest
from os.path import join
from crossmap.tokens import Kmerizer
from crossmap.data import CrossmapData
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
dataset_file = join(data_dir, "dataset.yaml")

test_map = dict(abcd=0, bcde=1, cdef=2, defg=3, efgh=4, fghi=5, ghij=6)


class CrossmapDataTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        self.builder = CrossmapData(test_map, Kmerizer(k=4))

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_tokenize_single_data(self):
        """convert a single string into a feature matrix"""

        result, name = self.builder.single({"data": "abcdef"}, "00")
        self.assertEqual(name, "00", "name is just returned back"),
        self.assertEqual(len(result), len(test_map),
                         "one row, all features")
        self.assertEqual(result[0], 1,
                         "first token is present, with value 1")
        self.assertEqual(sum(result), 3,
                         "input is split into three tokens")

    def test_tokenize_no_documents(self):
        """extract tokens with empty documents list"""

        result, names = self.builder.documents([])
        self.assertEqual(names, [])
        self.assertEqual(result, [])

    def test_tokenize_documents(self):
        """extract tokens from several documents on disk"""

        result, names = self.builder.documents([dataset_file])
        self.assertEqual(len(names), 6,
                         "dataset.yaml has six documents")
        self.assertEqual(sorted(names), ["A", "B", "C", "D", "U", "ZZ"],
                         "dataset.yaml has six documents")
        self.assertEqual(len(result), 6)
        self.assertEqual(len(result[0]), len(test_map))
        # entry for item "A" does not have requested features
        names_dict = {v:k for k,v in enumerate(names)}
        index_A = names_dict["A"]
        self.assertEqual(sum(result[index_A]), 0, "all values for item A zero")
        index_U = names_dict["U"]
        self.assertGreater(sum(result[index_U]), 1,
                           "item U has word ABCDEFG which matches features")

