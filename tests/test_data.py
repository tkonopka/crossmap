'''Tests for turning documents into tokens

@author: Tomasz Konopka
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

        sparse, name = self.builder.single("abcdef")
        # name array
        self.assertEqual(len(name), 1, "names array should have one item"),
        # structure of feature values
        result = sparse.toarray()
        self.assertEqual(result.shape, (1, len(test_map)),
                         "one row, all features")
        self.assertEqual(result[0,0], 1,
                         "first token is present, with value 1")
        self.assertEqual(sum(sum(result)), 3,
                         "input is split into three tokens")

    def test_tokenize_no_documents(self):
        """extract tokens with empty documents list"""

        sparse, names = self.builder.documents([])
        self.assertEqual(len(names), 0, "empty array")
        self.assertEqual(sparse.shape, (0, len(test_map)))

    def test_tokenize_documents(self):
        """extract tokens from several documents on disk"""

        sparse, names = self.builder.documents([dataset_file])
        self.assertEqual(len(names), 6,
                         "dataset.yaml has six documents")
        self.assertEqual(sorted(names), ["A", "B", "C", "D", "U", "ZZ"],
                         "dataset.yaml has six documents")
        result = sparse.toarray()
        self.assertEqual(result.shape, (6, len(test_map)))
        # entry for item "A" does not have requested features
        index_A = names["A"]
        self.assertEqual(sum(result[index_A]), 0, "all values for item A zero")
        index_U = names["U"]
        self.assertGreater(sum(result[index_U]), 1,
                           "item U has word ABCDEFG which matches features")

