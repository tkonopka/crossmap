'''Tests for turning datasets into tokens
'''

import unittest
from os.path import join
from crossmap.tokens import token_counts
from crossmap.tokens import kmers, Kmerizer

data_dir = join("tests", "testdata")
include_file = join(data_dir, "include.txt")
exclude_file = join(data_dir, "exclude.txt")
exclude_file2 = join(data_dir, "exclude_2.txt")
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

    def test_tokenize_documents(self):
        """obtain tokens from documents"""

        tokenizer = Kmerizer(k=5)
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["D"]
        self.assertEqual(len(result), 6)
        self.assertTrue("with" in result)
        # auxiliary data is weighted at 0.5
        self.assertEqual(result["with"], 0.5)
        # count sums primary data and auxiliary counts
        self.assertEqual(result["danie"], 1.5)
        self.assertEqual(result["aniel"], 1.5)

    def test_tokenize_entry_weight(self):
        """obtain relevant tokens, with a custom weight for auxiliary field"""

        tokenizer = Kmerizer(aux_weight=0.2)
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["A"]
        self.assertTrue("alice" in result)
        self.assertEqual(result["with"], 0.2)

    def test_tokenize_case_sensitive(self):
        """obtain tokens in case sensitive manner"""

        tokenizer = Kmerizer(k=10, case_sensitive=True)
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["U"]
        self.assertTrue("ABCDEFG" in result)
        self.assertEqual(result["ABCDEFG"], 1)

    def test_tokenize_case_insensitive(self):
        """obtain tokens, all in lowercase"""

        tokenizer = Kmerizer(k=10, case_sensitive=False)
        tokens = tokenizer.tokenize(dataset_file)
        result = tokens["U"]
        self.assertFalse("ABCDEFG" in result)
        self.assertTrue("abcdefg" in result)
        self.assertEqual(result["abcdefg"], 1)

    def test_count_all_tokens(self):
        """obtain summary of tokens in all documents"""

        tokenizer = Kmerizer(k=10, aux_weight=0.5)
        tokens = tokenizer.tokenize(dataset_file)
        result = token_counts(tokens)
        self.assertTrue("data" in result)
        self.assertGreater(result["with"], 1)
        self.assertEqual(result["abcdefg"], 1)
