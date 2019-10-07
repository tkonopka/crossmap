"""
Tests for manipulating csr vectors
"""

import unittest
from scipy.sparse import csr_matrix
from crossmap.csr import bytes_to_csr, csr_to_bytes


class CsrBytesTests(unittest.TestCase):
    """Conversion between bytes and csr objects"""

    def test_csr_to_bytes(self):
        """can convert a csr vector into bytes and back"""

        v = [0.0]*20
        v[3] = 0.4
        v[14] = 0.1
        v_1 = csr_matrix(v)
        v_2 = bytes_to_csr(csr_to_bytes(v_1), 20)
        self.assertEqual(sum(v_1.data), sum(v_2.data))

