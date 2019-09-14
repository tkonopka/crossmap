"""
Tests for handling distances between vectors
"""

import unittest
from numpy import array
from math import sqrt
from crossmap.distance import euc_dist, norm_euc_dist


class DistanceTests(unittest.TestCase):
    """Distance calculations"""

    def test_dist(self):
        """simple distances"""

        sq2 = sqrt(2)
        eucd = euc_dist
        self.assertEqual(eucd(array([0, 1.0]), array([1.0, 0])), sq2)
        self.assertEqual(eucd(array([0, 1.0, 0]), array([1.0, 0, 0])), sq2)

    def test_norm_dist(self):
        """simple distances between normalized vectors"""

        neucd = norm_euc_dist
        sq2 = sqrt(2)
        self.assertEqual(neucd(array([0, 2.0]), array([1.0, 0])), sq2)
        self.assertEqual(neucd(array([0, 2.0, 0]), array([1.0, 0, 0])), sq2)

