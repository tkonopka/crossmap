'''Tests for encoding documents into numeric vectors
'''

import unittest
from os.path import join
from crossmap.tokens import Kmerizer
from crossmap.encoder import CrossmapEncoder


data_dir = join("tests", "testdata")
dataset_file = join(data_dir, "dataset.yaml")
test_map = dict(abcd=(0,1), bcde=(1,1), cdef=(2,1),
                defg=(3,1), efgh=(4,1), fghi=(5,1),
                ghij=(6,1), hijk=(7,1), ijkl=(8,1))


class CrossmapEncoderTests(unittest.TestCase):
    """Turning text data into tokens"""

    def setUp(self):
        self.builder = CrossmapEncoder(test_map, Kmerizer(k=4))

    def test_encode_single_document(self):
        """process a single string into a feature matrix"""

        result, name = self.builder.document({"data": "abcdef"}, "00")
        arr = result.toarray()[0]
        self.assertEqual(name, "00", "name is just returned back"),
        self.assertEqual(len(arr), len(test_map), "one row, all features")
        self.assertGreater(arr[0], 0, "first token is present")
        self.assertEqual(sum([_>0 for _ in arr]), 3,
                         "input is split into three tokens")

    def test_encode_empty_doc(self):
        """process a document with no data"""

        doc = dict(data="")
        result, name = self.builder.document(doc, "X")
        arr = result.toarray()[0]
        self.assertEqual(len(arr), len(test_map), "")
        self.assertEqual(sum([_ for _ in arr]), 0)

    def test_encode_no_documents(self):
        """process an empty documents list"""

        result, names = self.builder.documents([])
        self.assertEqual(names, [])
        self.assertEqual(result, [])

    def test_encode_documents(self):
        """process several documents on disk"""

        result, ids_titles = self.builder.documents([dataset_file])
        self.assertEqual(len(ids_titles), 6,
                         "dataset.yaml has six documents")
        ids = [_[0] for _ in ids_titles]
        self.assertEqual(sorted(ids), ["A", "B", "C", "D", "U", "ZZ"],
                         "dataset.yaml has six documents")
        self.assertEqual(len(result), 6)
        r0 = result[0].toarray()[0]
        self.assertEqual(len(r0), len(test_map))
        # entry for item "A" does not have requested features
        names_dict = {v[0]:k for k, v in enumerate(ids_titles)}
        index_A = names_dict["A"]
        rA = result[index_A].toarray()[0]
        self.assertEqual(sum(rA), 0, "all values for item A zero")
        index_U = names_dict["U"]
        rU = result[index_U].toarray()[0]
        self.assertGreater(sum(rU), 0,
                           "item U has word ABCDEFG which matches features")

