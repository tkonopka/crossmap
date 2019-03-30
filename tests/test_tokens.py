'''Tests for turning datasets into tokens

@author: Tomasz Konopka
'''

import unittest
from os.path import join
from crossmap.tokens import Tokenizer, token_counts

data_dir = join("tests", "testdata")
include_file = join(data_dir, "test_include.txt")
exclude_file = join(data_dir, "test_exclude.txt")
exclude_file2 = join(data_dir, "test_exclude_2.txt")
dataset_file = join(data_dir, "dataset.yaml")


class TokenizerTests(unittest.TestCase):
    """Turning text data into tokens"""

    def test_init_include_file(self):
        """Configure a tokenizer using include tokens from files"""

        tokenizer = Tokenizer(include=include_file)
        self.assertTrue("abc" in tokenizer.include)
        self.assertFalse("this" in tokenizer.include)
        self.assertEqual(tokenizer.exclude, set())

    def test_init_exclude_file(self):
        """Configure a tokenizer using exclude tokens from files"""

        tokenizer = Tokenizer(exclude=exclude_file)
        self.assertTrue("the" in tokenizer.exclude)
        self.assertFalse("complex" in tokenizer.exclude)
        self.assertEqual(tokenizer.include, set())

    def test_init_exclude_many_files(self):
        """Configure a tokenizer using multiple files"""

        tokenizer = Tokenizer(exclude=[exclude_file, exclude_file2])
        self.assertTrue("the" in tokenizer.exclude)
        self.assertTrue("were" in tokenizer.exclude)
        self.assertTrue("is" in tokenizer.exclude)

    def test_tokenize_file(self):
        """obtain tokens for all entries in a dataset"""

        tokenizer = Tokenizer()
        tokens = tokenizer.tokenize(dataset_file)
        self.assertTrue("A" in tokens)
        self.assertTrue("ZZ" in tokens)
        self.assertGreater(len(tokens), 3)

    def test_tokenize_entry(self):
        """obtain relevant tokens"""

        tokenizer = Tokenizer(exclude=exclude_file)
        tokens = tokenizer.tokenize(dataset_file)
        # look at one entry "D"
        result = tokens["D"]
        self.assertEqual(len(result), 3)
        self.assertTrue("minimal" in result)
        self.assertEqual(result["data"], 1)
        self.assertEqual(result["entry"], 1)

    def test_tokenize_entry_aux(self):
        """obtain relevant tokens, including from auxiliary field"""

        tokenizer = Tokenizer(exclude=exclude_file)
        tokens = tokenizer.tokenize(dataset_file)
        # look at one entry "B"
        result = tokens["B"]
        self.assertTrue("simple" in result)
        self.assertLess(result["simple"], 1)

    def test_tokenize_entry_aux_weight(self):
        """obtain relevant tokens, including from auxiliary field"""

        tokenizer = Tokenizer(exclude=exclude_file, aux_weight=0.2)
        tokens = tokenizer.tokenize(dataset_file)
        # entry "A" has "Simple" in it auxiliary field
        result = tokens["A"]
        self.assertTrue("simple" in result)
        self.assertEqual(result["simple"], 0.2)


    def test_tokenize_case_sensitive(self):
        """obtain tokens in case sensitive manner"""

        tokenizer = Tokenizer(case_sensitive=True)
        tokens = tokenizer.tokenize(dataset_file)
        # entry "A" has "Simple" in it auxiliary field
        result = tokens["U"]
        self.assertTrue("ABCDEFG" in result)
        self.assertEqual(result["ABCDEFG"], 1)

    def test_tokenize_case_insensitive(self):
        """obtain tokens, all in lowercase"""

        tokenizer = Tokenizer(case_sensitive=False)
        tokens = tokenizer.tokenize(dataset_file)
        # entry "A" has "Simple" in it auxiliary field
        result = tokens["U"]
        self.assertFalse("ABCDEFG" in result)
        self.assertTrue("abcdefg" in result)
        self.assertEqual(result["abcdefg"], 1)

    def test_count_all_tokens(self):
        """obtain summary of tokens in all documents"""

        tokenizer = Tokenizer(exclude=exclude_file, aux_weight=0.5)
        tokens = tokenizer.tokenize(dataset_file)
        result = token_counts(tokens)
        self.assertTrue("data" in result)
        self.assertGreater(result["data"], 2)
        self.assertEqual(result["abcdefg"], 1)
