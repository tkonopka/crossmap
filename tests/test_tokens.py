"""
Tests for turning datasets into tokens
"""

import unittest
from os.path import join
from crossmap.tokens import token_counts
from crossmap.tokens import kmers, Kmerizer
from crossmap.tools import yaml_document

data_dir = join("tests", "testdata")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")
arrays_file = join(data_dir, "dataset-arrays.yaml")


class KmersTests(unittest.TestCase):
    """extracting kmers in a string"""

    def test_kmers_short(self):
        result = kmers("ab", 3)
        self.assertEqual(result, ["ab"])

    def test_kmers_empty(self):
        with self.assertRaises(Exception) as e:
            kmers(None, 3)

    def test_kmers_simple(self):
        result = kmers("abcde", 3)
        self.assertEqual(result, ["abc", "bcd", "cde"])


class KmerizerTests(unittest.TestCase):
    """Turning text data into kmer tokens"""

    def test_init_small_k(self):
        """Configure a tokenizer with custom k"""

        tokenizer = Kmerizer(k=2)
        self.assertEqual(tokenizer.k, 2)

    def test_init_default(self):
        """Configure a tokenizer with default alphabet"""

        tokenizer = Kmerizer()
        self.assertTrue("a" in tokenizer.alphabet)
        self.assertTrue("0" in tokenizer.alphabet)

    def test_tokenize_file(self):
        """obtain tokens for all entries in a dataset"""

        tokenizer = Kmerizer()
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        self.assertTrue("A" in tokens)
        self.assertTrue("ZZ" in tokens)
        self.assertGreater(len(tokens), 3)

    def test_tokenize_entry_structure(self):
        """obtain tokens for every component of a document"""

        tokenizer = Kmerizer()
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["A"]
        self.assertTrue("data" in result)
        self.assertTrue("aux_pos" in result)
        # aux_neg is not in the result because the dataset does not define aux_neg
        self.assertFalse("aux_neg" in result)

    def test_tokenize_entry_structure_aux_neg(self):
        """obtain tokens also from aux_neg fields"""

        tokenizer = Kmerizer()
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["C"]
        self.assertTrue("aux_neg" in result)
        self.assertTrue("bob" in result["aux_neg"])
        self.assertEqual(result["aux_neg"]["bob"], 1)

    def test_tokenize_documents(self):
        """obtain tokens from documents"""

        tokenizer = Kmerizer(k=5)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["D"]
        # data component should only be based on "Daniel"
        self.assertEqual(len(result["data"]), 2)
        self.assertTrue("danie" in result["data"])
        # aux_pos component will have other items
        self.assertTrue("with" in result["aux_pos"])
        self.assertEqual(result["aux_pos"]["with"], 1)
        self.assertEqual(result["aux_pos"]["danie"], 1)
        self.assertEqual(result["aux_pos"]["aniel"], 1)

    def test_tokenize_case_sensitive(self):
        """obtain tokens in case sensitive manner"""

        tokenizer = Kmerizer(k=10, case_sensitive=True)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["U"]["data"]
        self.assertTrue("ABCDEFG" in result)
        self.assertEqual(result["ABCDEFG"], 1)

    def test_tokenize_case_insensitive(self):
        """obtain tokens, all in lowercase"""

        tokenizer = Kmerizer(k=10, case_sensitive=False)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["U"]["data"]
        self.assertFalse("ABCDEFG" in result)
        self.assertTrue("abcdefg" in result)
        self.assertEqual(result["abcdefg"], 1)

    def test_count_all_tokens(self):
        """obtain summary of tokens in all documents"""

        tokenizer = Kmerizer(k=10)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = token_counts(tokens)
        self.assertTrue("data" in result)
        self.assertGreater(result["with"], 1)
        self.assertEqual(result["abcdefg"], 1)

    def test_tokenize_with_nondefault_alphanet(self):
        """tokenizing with alphabet with missing letters introduces spaces"""

        tokenizer = Kmerizer(k=5, alphabet="bcdefghijklmnopqrstuvwxyz")
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        # item Alice - has a word just with letter A
        dataA = tokens["A"]["data"]
        auxA = tokens["A"]["aux_pos"]
        # letter "A" can turn into " " and reduce to ""
        # avoid tokens that are empty
        self.assertFalse("a" in dataA)
        keysA = list(auxA.keys())
        for k in keysA:
            self.assertNotEqual(k, "")
        # item Daniel - has letter a on a boundary of k=5
        keysD = list(tokens["D"]["data"].keys())
        # "Daniel" can create "D niel" which can kmerize to " niel"
        # avoid tokens that start with a space
        self.assertEqual(keysD, [_.strip() for _ in keysD])


class KmerizerArraysTests(unittest.TestCase):
    """Tokenize when yaml data is formatted as an array"""

    tokenizer = Kmerizer(k=5)

    def setUp(self):
        tokens = dict()
        with open(arrays_file, "rt") as f:
            for id, doc in yaml_document(f):
                tokens[id] = self.tokenizer.tokenize(doc)
        self.tokens = tokens

    def test_tokenize_arrays_without_quotes(self):
        """tokenize when yaml array does not have quotes"""

        result = self.tokens["without"]["aux_pos"]
        self.assertTrue("abcde" in result)
        self.assertTrue("mnopq" in result)
        self.assertTrue("nopqr" in result)

    def test_tokenize_arrays_with_quotes(self):
        """tokenize when yaml array has quote around each item"""

        result = self.tokens["with"]["aux_pos"]
        self.assertTrue("abc12" in result)
        self.assertTrue("bc123" in result)
        self.assertTrue("abc78" in result)
        self.assertTrue("bc789" in result)

