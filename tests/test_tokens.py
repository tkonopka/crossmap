'''Tests for turning datasets into tokens
'''

import unittest
from os.path import join
from crossmap.tokens import token_counts
from crossmap.tokens import kmers, Kmerizer

data_dir = join("tests", "testdata")
include_file = join(data_dir, "include.txt")
dataset_file = join(data_dir, "dataset.yaml")


class KmersTests(unittest.TestCase):
    """extracting kmers in a string"""

    def test_kmers_short(self):
        result = kmers("ab", 3)
        self.assertEqual(result, ["ab"])

    def test_kmers_empty(self):
        with self.assertRaises(Exception) as e:
            result = kmers(None, 3)

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
        tokens = tokenizer.tokenize(dataset_file)
        self.assertTrue("A" in tokens)
        self.assertTrue("ZZ" in tokens)
        self.assertGreater(len(tokens), 3)

    def test_tokenize_entry_structure(self):
        """obtain tokens for every component of a document"""

        tokenizer = Kmerizer()
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["A"]
        self.assertTrue("data" in result)
        self.assertTrue("aux_pos" in result)
        # aux_neg is not in the result because the dataset does not define aux_neg
        self.assertFalse("aux_neg" in result)

    def test_tokenize_entry_structure_aux_neg(self):
        """obtain tokens also from aux_neg fields"""

        tokenizer = Kmerizer()
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["C"]
        self.assertTrue("aux_neg" in result)
        self.assertTrue("bob" in result["aux_neg"])
        self.assertEqual(result["aux_neg"]["bob"], 1)

    def test_tokenize_documents(self):
        """obtain tokens from documents"""

        tokenizer = Kmerizer(k=5)
        tokens = tokenizer.tokenize(dataset_file)
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
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["U"]["data"]
        self.assertTrue("ABCDEFG" in result)
        self.assertEqual(result["ABCDEFG"], 1)

    def test_tokenize_case_insensitive(self):
        """obtain tokens, all in lowercase"""

        tokenizer = Kmerizer(k=10, case_sensitive=False)
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["U"]["data"]
        self.assertFalse("ABCDEFG" in result)
        self.assertTrue("abcdefg" in result)
        self.assertEqual(result["abcdefg"], 1)

    def test_count_all_tokens(self):
        """obtain summary of tokens in all documents"""

        tokenizer = Kmerizer(k=10)
        tokens = tokenizer.tokenize(dataset_file)
        result = token_counts(tokens)
        self.assertTrue("data" in result)
        self.assertGreater(result["with"], 1)
        self.assertEqual(result["abcdefg"], 1)
