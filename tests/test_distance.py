'''Tests for handling distances between vectors
'''

import unittest
from math import sqrt
from crossmap.distance import vec_norm, normalize_vec, all_zero
from crossmap.distance import euc_dist, euc_sq_dist, norm_euc_dist


class VecNormTests(unittest.TestCase):
    """Vector normalization"""

    def test_norm_1(self):
        """compute the norm of simple vectors"""

        self.assertEqual(vec_norm([0,1,0]), 1)
        self.assertEqual(vec_norm([0,1]), 1)
        self.assertEqual(vec_norm([1]), 1)

    def test_norm_2(self):
        """compute the norm with multi-component vectors"""

        self.assertEqual(vec_norm([0,1,1]), sqrt(2))
        self.assertEqual(vec_norm([1,2]), sqrt(5))

    def test_all_zero_True(self):
        """produce a unit-norm vector"""

        self.assertEqual(all_zero([0, 0, 0]), 1)
        self.assertEqual(all_zero([0]), 1)

    def test_all_zero_False(self):
        """produce a unit-norm vector"""

        self.assertEqual(all_zero([0.4, 0.0, 0.0]), 0)
        self.assertEqual(all_zero([0.0, 0.0, -0.2]), 0)

    def test_normalize(self):
        """produce a unit-norm vector"""

        self.assertEqual(normalize_vec([0, 2, 0]), [0, 1, 0])
        self.assertEqual(normalize_vec([4, 0]), [1, 0])

    def test_normalize_null_vector(self):
        """produce a unit-norm vector"""

        self.assertEqual(normalize_vec([0, 0]), [0, 0])


class DistanceTests(unittest.TestCase):
    """Distance calculations"""

    def test_dist(self):
        """simple distances"""

        self.assertEqual(euc_dist([0,1], [1,0]), sqrt(2))
        self.assertEqual(euc_dist([0,1,0], [1,0,0]), sqrt(2))

    def test_norm_dist(self):
        """simple distances between normalized vectors"""

        self.assertEqual(norm_euc_dist([0,2], [1,0]), sqrt(2))
        self.assertEqual(norm_euc_dist([0,2,0], [1,0,0]), sqrt(2))

    def test_sq_dist(self):
        """simple distances"""

        self.assertEqual(euc_sq_dist([0,1], [1,0]), 2)
        self.assertEqual(euc_sq_dist([0,1,0], [1,0,0]), 2)

