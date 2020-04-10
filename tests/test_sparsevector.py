"""
Tests for working with sparse data using dicts
"""

import unittest
from scipy.sparse import csr_matrix
from crossmap.sparsevector import Sparsevector


class SparsevectorTests(unittest.TestCase):
    """Conversion between bytes and csr objects"""

    def test_init_add(self):
        """create a blank vector and add into it"""

        v_csr = csr_matrix([0, 0, 1, 0, 0, 4, 0])
        result = Sparsevector()
        result.add_csr(v_csr)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[2], 1)
        self.assertEqual(result.data[5], 4)

    def test_init_autoadd(self):
        """create and add in a single step"""

        v_csr = csr_matrix([0, 0, 1, 0, 0, 4, 0])
        result = Sparsevector(v_csr)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[2], 1)
        self.assertEqual(result.data[5], 4)

    def test_add_two_csr(self):
        """can convert a csr vector into bytes and back"""

        v1_csr = csr_matrix([0, 0, 1, 0, 0, 4, 0])
        v2_csr = csr_matrix([0, 3, 1, 0, 0, 0, 0])
        result = Sparsevector()
        result.add_csr(v1_csr).add_csr(v2_csr)
        self.assertEqual(len(result.data), 3)
        self.assertEqual(result.data[1], 3)
        self.assertEqual(result.data[2], 2)
        self.assertEqual(result.data[5], 4)

    def test_add_multiplier(self):
        """can add using a multiplier"""

        v1_csr = csr_matrix([0, 0, 1, 0, 0, 4, 0])
        result = Sparsevector()
        result.add_csr(v1_csr, 1.5)
        self.assertEqual(len(result.data), 2)
        self.assertEqual(result.data[2], 1.5)
        self.assertEqual(result.data[5], 6.0)

    def test_to_csr(self):
        """convert dictionary to a csr_representation"""

        temp = Sparsevector()
        temp.add_csr(csr_matrix([0, 1, 0, 0, 0, 1, 0, 0]))
        temp.add_csr(csr_matrix([1, 0, 0, 0, 0, 1.5, 0, 0]))
        result = temp.to_csr(8)
        result_dense = (result.toarray())[0]
        self.assertEqual(len(result_dense), 8)
        self.assertEqual(result_dense[0], 1.0)
        self.assertEqual(result_dense[1], 1.0)
        self.assertEqual(result_dense[5], 2.5)

    def test_to_csr_threshold(self):
        """convert dictionary to a csr_representation, with a threshold"""

        temp = Sparsevector()
        temp.add_csr(csr_matrix([0, 2, 0, 0.3, 0, 1, 0.5, 0.1]))
        result = temp.to_csr(8, 0.2)
        result_dense = (result.toarray())[0]
        self.assertEqual(len(result_dense), 8)
        self.assertEqual(result_dense[0], 0.0)
        self.assertEqual(result_dense[1], 2.0)
        self.assertEqual(result_dense[3], 0.0)
        self.assertEqual(result_dense[6], 0.5)
        self.assertEqual(result_dense[7], 0.0)

    def test_to_str(self):
        """write out a string representation"""

        temp = Sparsevector()
        temp.add_csr(csr_matrix([0, 1, 0, 0, 0, 1, 0, 0]))
        temp.add_csr(csr_matrix([1, 0, 0, 0, 0, 1.5, 0, 0]))
        result = str(temp)
        self.assertTrue("1" in result)
        self.assertTrue("2.5" in result)



