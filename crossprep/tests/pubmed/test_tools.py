'''Tests for various tools in pubmed package

@author: Tomasz Konopka
'''


import unittest
from crossprep.pubmed.tools import parse_indexes


class ParseIndexesTests(unittest.TestCase):
    """Parsing strings with indexes."""

    def test_parse_indexes_raises(self):
        """parsing indexes accepts only integers, comma, hyphen"""

        with self.assertRaises(Exception) as e:
            parse_indexes("1-4#,2")
        with self.assertRaises(Exception) as e:
            parse_indexes("1-4-10")

    def test_parse_indexes_single(self):
        """can parse string inputs into a list of integers"""

        one = parse_indexes("1")
        self.assertEqual(one, [1])
        two = parse_indexes("2")
        self.assertEqual(two, [2])

    def test_parse_indexes_comma(self):
        """can parse comma,separated indexes"""

        result = parse_indexes("1,4,6")
        self.assertEqual(result, [1,4,6])
        result = parse_indexes("1,4,6,2")
        self.assertEqual(result, [1,2,4,6])

    def test_parse_indexes_sorting(self):
        """can parse indexes, output is sorted"""

        result = parse_indexes("1,4,6,2,10,1,3")
        self.assertEqual(result, [1,2,3,4,6,10])

    def test_parse_indexes_hyphen(self):
        """can parse comma,separated indexes"""

        result = parse_indexes("1-4")
        self.assertEqual(result, [1,2,3,4])

    def test_parse_indexes_mixed(self):
        """can parse comma and hyphen mixed input"""

        result = parse_indexes("1-4,10,20-22")
        self.assertEqual(result, [1,2,3,4,10,20,21,22])
