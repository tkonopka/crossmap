"""
Tests for manipulating csr vectors
"""

import unittest
from numpy import array
from scipy.sparse import csr_matrix
from crossmap.csr import \
    bytes_to_csr, \
    csr_to_bytes, \
    normalize_csr, \
    threshold_csr, \
    cap_csr, \
    dimcollapse_csr, \
    add_sparse_skip, \
    harmonic_multiply_sparse, \
    max_multiply_sparse
from crossmap.vectors import sparse_to_dense


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


class CsrNormTests(unittest.TestCase):
    """csr vector normalization"""

    def test_normalize_csr(self):
        """produce a unit-norm vector from csr"""

        n_csr = normalize_csr
        result1 = sparse_to_dense(n_csr(csr_matrix([0.0, 2.0, 0.0])))
        self.assertListEqual(list(result1), [0.0, 1.0, 0.0])
        result2 = sparse_to_dense(n_csr(csr_matrix([4.0, 0.0])))
        self.assertListEqual(list(result2), [1.0, 0.0])

    def test_normalize_csr_in_place(self):
        """produce a unit-norm vector from csr (in place)"""

        vec = csr_matrix([0.0, 2.0, 0.0])
        normalize_csr(vec)
        self.assertListEqual(list(sparse_to_dense(vec)), [0.0, 1.0, 0.0])


class CsrThresholdTests(unittest.TestCase):
    """Adjusting csr vectors via thresholds"""

    def test_threshold_positives(self):
        """using a simple vector with positive values"""

        a = csr_matrix([0.0, 0.1, 0.5, 0.35,
                        0.9, 0.0, 0.0, 0.4])
        result = threshold_csr(a, 0.3)
        expected = [0.0, 0.0, 0.5, 0.35,
                    0.9, 0.0, 0.0, 0.4]
        self.assertListEqual(list(sparse_to_dense(result)), expected)
        self.assertEqual(result.shape, (1, 8))

    def test_threshold_w_negatives(self):
        """threshold preserves very negative values"""

        b = csr_matrix([0.0, 0.1, -0.5, 0.35,
                        0.9, -0.2, 0.0, -0.4])
        result = threshold_csr(b, 0.3)
        expected = [0.0, 0.0, -0.5, 0.35,
                    0.9, 0.0, 0.0, -0.4]
        self.assertListEqual(list(sparse_to_dense(result)), expected)
        self.assertEqual(result.shape, (1, 8))

    def test_threshold_to_zeros(self):
        """threshold and all values are set to zero"""

        x = csr_matrix([0.0, 0.0, 0.0, 0.4,
                        0.2, 0.0, -0.8, 0.1])
        result = threshold_csr(x, 2)
        self.assertEqual(sum(sparse_to_dense(result)), 0)
        self.assertEqual(result.shape, (1, 8))

    def test_cap(self):
        """impose a ceiling on vector values, +ve and -ve"""

        x = csr_matrix([0.0, 0.0, 0.4, 0.2, -0.4, 0.0])
        result = cap_csr(x, 0.3)
        self.assertListEqual(list(result.data), [0.3, 0.2, -0.3])


class CsrAddTests(unittest.TestCase):
    """Adding a dense array and a sparse array"""

    def test_simple(self):
        """simple adding"""

        arr = array([1.0, 1.0, 1.0, 1.0, 1.0])
        a = csr_matrix([0.5, 0.0, -0.5, 0.0, 2.5])
        result = add_sparse_skip(arr, a.data, a.indices)
        expected = [1.5, 1.0, 0.5, 1.0, 3.5]
        self.assertListEqual(list(result), expected)
        self.assertListEqual(list(arr), expected)


class CsrMultiplicationTests(unittest.TestCase):
    """Multiply a dense array and a sparse array"""

    def test_harmonic_simple(self):
        """simple multiplying, using harmonic"""

        arr = array([1.0, 2.0, 3.0, 4.0, 5.0])
        a = csr_matrix([0.5, 0.0, 0.5, 0.0, 1.0])
        result = harmonic_multiply_sparse(arr, a.data, a.indices, 2.0)
        expected = [0.5*(2/3), 0.5*(6/5), 1.0*(10/7)]
        self.assertListEqual(list(result), expected)

    def test_max_simple(self):
        """simple multiplying, using harmonic"""

        arr = array([1.5, 2.0, 3.0, 4.0, 5.0])
        a = csr_matrix([0.5, 0.0, 0.5, 0.0, 1.0])
        result = max_multiply_sparse(arr, a.data, a.indices, 2.0)
        expected = [0.5*1.5, 0.5*2.0, 1.0*2.0]
        self.assertListEqual(list(result), expected)


class CsrDimensionalCollapseTests(unittest.TestCase):
    """csr vector collapse"""

    def test_raw_collapse(self):
        """raw collapse, setting values to zero without normalization"""

        a = csr_matrix([0.0, 0.1, 0.5, 0.35,
                        0.9, 0.0, 0.0, 0.4])
        result = dimcollapse_csr(a, set([0,1,2,3]), normalize=False)
        expected = [0.0, 0.1, 0.5, 0.35,
                    0.0, 0.0, 0.0, 0.0]
        self.assertListEqual(list(sparse_to_dense(result)), expected)
        self.assertEqual(result.shape, (1, 8))

    def test_normalized_collapse(self):
        """collapse to dimension, with global rescaling/normalization"""

        a = csr_matrix([0.0, 0.1, 0.5, 0.35,
                        0.9, 0.0, 0.0, 0.4])
        result = dimcollapse_csr(a, set([0,1,2,3]), normalize=True)
        result_dense = sparse_to_dense(result)
        self.assertEqual(result_dense[4], 0.0)
        self.assertGreater(result_dense[1], 0.1)

