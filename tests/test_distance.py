"""
Tests for handling distances between vectors
"""

import unittest
from numpy import array
from math import sqrt
from crossmap.distance import num_nonzero
from crossmap.distance import vec_norm, normalize_vec, all_zero
from crossmap.distance import euc_dist, norm_euc_dist


class VecNormTests(unittest.TestCase):
    """Vector normalization"""

    def test_norm_1(self):
        """compute the norm of simple vectors"""

        self.assertEqual(vec_norm(array([0,1,0])), 1)
        self.assertEqual(vec_norm(array([0,1])), 1)
        self.assertEqual(vec_norm(array([1])), 1)

    def test_norm_2(self):
        """compute the norm with multi-component vectors"""

        self.assertEqual(vec_norm(array([0,1,1])), sqrt(2))
        self.assertEqual(vec_norm(array([1,2])), sqrt(5))

    def test_all_zero_True(self):
        """produce a unit-norm vector"""

        self.assertEqual(all_zero(array([0, 0, 0])), 1)
        self.assertEqual(all_zero(array([0])), 1)

    def test_all_zero_False(self):
        """produce a unit-norm vector"""

        self.assertEqual(all_zero(array([0.4, 0.0, 0.0])), 0)
        self.assertEqual(all_zero(array([0.0, 0.0, -0.2])), 0)

    def test_num_nonzero(self):
        """produce a unit-norm vector"""

        self.assertEqual(num_nonzero(array([0.0, 0.0, 0.0])), 0)
        self.assertEqual(num_nonzero(array([0.0, 0.0, -0.2])), 1)

    def test_normalize(self):
        """produce a unit-norm vector"""

        nvec = normalize_vec
        self.assertListEqual(list(nvec(array([0, 2, 0]))), [0, 1, 0])
        self.assertListEqual(list(nvec(array([4, 0]))), [1, 0])

    def test_normalize_null_vector(self):
        """produce a unit-norm vector"""
        nvec = normalize_vec
        self.assertListEqual(list(nvec(array([0, 0]))), [0, 0])


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

