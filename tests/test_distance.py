'''Tests for handling distances between vectors
'''

import unittest
from math import sqrt
from crossmap.distance import vec_norm, euc_dist, euc_sq_dist


class VecNormTests(unittest.TestCase):
    """Vector normalization"""

    def test_norm_1(self):
        """convert a single string into a feature matrix"""

        self.assertEqual(vec_norm([0,1,0]), 1)
        self.assertEqual(vec_norm([0,1]), 1)
        self.assertEqual(vec_norm([1]), 1)

    def test_norm_1(self):
        """convert a single string into a feature matrix"""

        self.assertEqual(vec_norm([0,1,1]), sqrt(2))
        self.assertEqual(vec_norm([1,2]), sqrt(5))


class DistanceTests(unittest.TestCase):
    """Distance calculations"""

    def test_dist(self):
        """simple distances"""

        self.assertEqual(euc_dist([0,1], [1,0]), sqrt(2))
        self.assertEqual(euc_dist([0,1,0], [1,0,0]), sqrt(2))

    def test_sq_dist(self):
        """simple distances"""

        self.assertEqual(euc_sq_dist([0,1], [1,0]), 2)
        self.assertEqual(euc_sq_dist([0,1,0], [1,0,0]), 2)

