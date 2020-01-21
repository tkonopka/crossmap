"""
Tests for encoding documents into numeric vectors
"""

import unittest
from math import sqrt
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
        """process a document with a single string in data"""

        result = self.builder.document({"data": "abcdef"})
        arr = result.toarray()[0]
        self.assertEqual(len(arr), len(test_map), "one row, all features")
        self.assertGreater(arr[0], 0, "first token is present")
        self.assertEqual(sum([_>0 for _ in arr]), 3,
                         "input is split into three tokens")

    def test_encode_empty_doc(self):
        """process a document with no data"""

        doc = dict(data="")
        result = self.builder.document(doc)
        arr = result.toarray()[0]
        self.assertEqual(len(arr), len(test_map), "")
        self.assertEqual(sum([_ for _ in arr]), 0)

    def test_encode_no_documents(self):
        """process an empty documents list"""

        ids = [_id for _item, _id, _title in self.builder.documents([])]
        self.assertEqual(ids, [])

    def test_encode_documents(self):
        """process several documents on disk"""

        result, ids, titles = [], [], []
        for _d, _id, _title in self.builder.documents([dataset_file]):
            result.append(_d)
            ids.append(_id)
            titles.append(_title)
        self.assertEqual(len(ids), 6,
                         "dataset.yaml has six documents")
        self.assertEqual(sorted(ids), ["A", "B", "C", "D", "U", "ZZ"],
                         "dataset.yaml has six documents")
        self.assertEqual(len(result), 6)
        r0 = result[0].toarray()[0]
        self.assertEqual(len(r0), len(test_map))
        # entry for item "A" does not have requested features
        names_dict = {ids[_]:_ for _ in range(len(ids))}
        index_a = names_dict["A"]
        r_a = result[index_a].toarray()[0]
        self.assertEqual(sum(r_a), 0, "all values for item A zero")
        index_u = names_dict["U"]
        r_u = result[index_u].toarray()[0]
        self.assertGreater(sum(r_u), 0,
                           "item U has word ABCDEFG which matches features")

    def test_encode_document_w_repeated_otkens(self):
        """process a single document that contains a token twice"""

        result1 = self.builder.document({"data": "abcd fghi"})
        result2 = self.builder.document({"data": "abcd abcd abcd abcd fghi"})
        arr1 = result1.toarray()[0]
        arr2 = result2.toarray()[0]
        # index of token for abcd
        abcd = test_map["abcd"][0]
        self.assertGreater(arr1[abcd], 0)
        # the second vector should have more weight on abcd that first vector
        # because 'abcde' is repeated
        self.assertGreater(arr2[abcd], arr1[abcd])
        # under proportional scaling, second vector should have 4/5 of
        # total weight assigned to abcd
        # but the encoder should be log-penalizing repeat tokens.
        naive_arr = [4.0/sqrt(17), 1.0/sqrt(17)]
        self.assertLess(arr2[abcd], naive_arr[0])
