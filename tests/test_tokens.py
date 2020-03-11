"""
Tests for turning datasets into tokens
"""

import unittest
from os.path import join
from crossmap.tokenizer import token_counts
from crossmap.tokenizer import kmers, Kmerizer

data_dir = join("tests", "testdata")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")
specialcases_file = join(data_dir, "documents-special-cases.yaml")


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

    def test_init_small_k_array(self):
        """Configure a tokenizer with custom k (one value)"""

        tokenizer = Kmerizer(k=[2, 3])
        self.assertEqual(tokenizer.k, (2, 3))

    def test_init_small_k_int(self):
        """Configure a tokenizer with custom k (one value)"""

        tokenizer = Kmerizer(k=2)
        self.assertEqual(tokenizer.k, (2, 4))

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
        # data_neg is not in the result because the dataset does not define data_neg
        self.assertFalse("data_neg" in result)

    def test_tokenize_entry_structure_aux_neg(self):
        """obtain tokens also from aux_neg fields"""

        tokenizer = Kmerizer()
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["C"]
        self.assertTrue("aux_neg" in result)
        self.assertTrue("bob" in result["aux_neg"])
        self.assertEqual(result["aux_neg"].data["bob"], 1)

    def test_tokenize_documents(self):
        """obtain tokens from documents"""

        tokenizer = Kmerizer(k=5)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["D"]
        # data component should only be based on:
        #  Daniel (2 tokens), starts (2 tokens), with D
        self.assertEqual(len(result["data"]), 6)
        self.assertTrue("danie" in result["data"])
        self.assertTrue("with" in result["data"])
        # weights of short tokens should have value 1,
        # parts of longer word should have lower values
        self.assertEqual(result["data"].data["with"], 1.0)
        self.assertLess(result["data"].data["start"], 1.0)
        self.assertLess(result["data"].data["tarts"], 1.0)

    def test_tokenize_case_sensitive(self):
        """obtain tokens in case sensitive manner"""

        tokenizer = Kmerizer(k=10, case_sensitive=True)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["U"]["data"]
        self.assertTrue("ABCDEFG" in result)
        self.assertEqual(result.data["ABCDEFG"], 1)

    def test_tokenize_case_insensitive(self):
        """obtain tokens, all in lowercase"""

        tokenizer = Kmerizer(k=10, case_sensitive=False)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = tokens["U"]["data"]
        self.assertFalse("ABCDEFG" in result)
        self.assertTrue("abcdefg" in result)
        self.assertEqual(result.data["abcdefg"], 1)

    def test_count_all_tokens(self):
        """obtain summary of tokens in all documents"""

        tokenizer = Kmerizer(k=10)
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        result = token_counts(tokens)
        self.assertTrue("data" in result)
        self.assertGreater(result.data["with"], 1)
        self.assertEqual(result.data["abcdefg"], 1)

    def test_tokenize_with_nondefault_alphanet(self):
        """tokenizing with alphabet with missing letters introduces spaces"""

        # custom tokenizer that does not allow the letter "a"
        tokenizer = Kmerizer(k=5, alphabet="bcdefghijklmnopqrstuvwxyz")
        tokens = dict()
        for id, data in tokenizer.tokenize_path(dataset_file):
            tokens[id] = data
        # item Alice - has a word just with letter A
        dataA = tokens["A"]["data"].data
        # letter "A" can turn into " " and reduce to ""
        # avoid tokens that are empty
        self.assertFalse("a" in dataA)
        keysA = list(dataA.keys())
        for k in keysA:
            self.assertNotEqual(k, "")
        # item Daniel - has letter "a" on a boundary of k=5
        keysD = list(tokens["D"]["data"].data.keys())
        # "Daniel" can create "D niel" which can kmerize to " niel"
        # avoid tokens that start with a space
        self.assertEqual(keysD, [_.strip() for _ in keysD])


class KmerizerSpecialCasesTests(unittest.TestCase):
    """Tokenize when yaml data has special cases"""

    tokenizer = Kmerizer(k=20)

    @classmethod
    def setUpClass(cls):
        tokens = dict()
        for id, data in cls.tokenizer.tokenize_path(specialcases_file):
            tokens[id] = data
        cls.tokens = tokens

    def test_tokenize_arrays_without_quotes(self):
        """tokenize when yaml array does not have quotes"""

        result = self.tokens["array_without_quotes"]["data"]
        self.assertTrue("abcdef" in result)
        self.assertTrue("mnopqr" in result)

    def test_tokenize_arrays_with_quotes(self):
        """tokenize when yaml array has quote around each item"""

        result = self.tokens["array_with_quotes"]["data"]
        self.assertTrue("abc123" in result)
        self.assertTrue("abc789" in result)

    def test_tokenize_unicode(self):
        """tokenize when yaml array does not have quotes"""

        result = self.tokens["alpha"]
        self.assertTrue("alpha" in result["data"])

    def test_tokenize_multiline(self):
        """tokenize when yaml has empty lines within items"""

        result = self.tokens["multiline"]
        self.assertTrue("multiple" in result["data"])

    def test_tokenize_data_dictionaries(self):
        """tokenize when data is itself a dictionary"""

        result = self.tokens["dictionary"]
        # content of dictionary should be tokenized
        self.assertTrue("alpha" in result["data"])
        # keys to the dictionary should not be tokenized
        self.assertFalse("short" in result["data"])
        self.assertFalse("long" in result["data"])

    def test_tokenize_data_with_slashes(self):
        """tokenize when data has slashes"""

        result = self.tokens["slashes"]
        self.assertEqual(len(result["data"]), 3)
        self.assertTrue("a" in result["data"])
        self.assertTrue("b" in result["data"])
        self.assertTrue("c" in result["data"])
