"""
Tests for counting tokens and number of updates
"""

import unittest
from crossmap.tokencounter import TokenCounter


class TokenCounterTests(unittest.TestCase):
    """keep track of values"""

    def test_count_singles(self):
        counter = TokenCounter()
        counter.add("a", 0.5)
        counter.add("b", 1.2)
        self.assertEqual(counter.data["a"], 0.5)
        self.assertEqual(counter.data["b"], 1.2)
        self.assertEqual(counter.count["a"], 1)
        self.assertEqual(counter.count["b"], 1)

    def test_count_repeated(self):
        counter = TokenCounter()
        counter.add("a", 0.5)
        counter.add("b", 1.2)
        counter.add("a", 1.2)
        self.assertEqual(counter.data["a"], 1.7)
        self.assertEqual(counter.data["b"], 1.2)
        self.assertEqual(counter.count["a"], 2)
        self.assertEqual(counter.count["b"], 1)



