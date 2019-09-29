"""
Tests for working with sparse vectors
"""

import numpy as np
import unittest
from numpy import array
from math import sqrt
from scipy.sparse import csr_matrix, vstack
from crossmap.vectors import csr_residual, vec_decomposition
from crossmap.vectors import num_nonzero, all_zero
from crossmap.vectors import vec_norm, normalize_vec, normalize_csr
from crossmap.vectors import sparse_to_dense

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

    def test_normalize_csr(self):
        """produce a unit-norm vector from csr"""

        ncsr = normalize_csr
        result1 = sparse_to_dense(ncsr(csr_matrix([0, 2, 0])))
        self.assertListEqual(list(result1), [0, 1, 0])
        result2 = sparse_to_dense(ncsr(csr_matrix([4,0])))
        self.assertListEqual(list(result2), [1, 0])



class VecResidualTests(unittest.TestCase):
    """computing residuals for vector decomposition"""

    def test_residual_from_null_vector(self):
        """starting with a null vector, residuals are also null"""
        v = csr_matrix([0, 0, 0, 0])
        mat = csr_matrix([0, 1, 0, 0])
        result = csr_residual(v, mat)
        self.assertListEqual(list(result.toarray()[0]), list(v.toarray()[0]))

    def test_residual_with_null_matrix(self):
        """subtracting nothing return original input"""
        v = csr_matrix([0, 0, 1, 0])
        mat = csr_matrix([])
        result = csr_residual(v, mat)
        expected = [0, 0, 1, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null(self):
        """subtracting can lead to a null vector"""
        v = csr_matrix([0, 0, 1, 0])
        mat = csr_matrix([0, 0, 1, 0])
        result = csr_residual(v, mat)
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null_two_steps(self):
        """subtracting two vectors can eventually lead to a null vector"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0], [0, 0, 0, 1]])
        result = csr_residual(v, mat)
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null_three_steps(self):
        """subtracting two vectors can eventually lead to a null vector"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 1]])
        result = csr_residual(v, mat, [1, 0.5, 0.5])
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_partial(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([0, 0, 1, 0])
        result = csr_residual(v, mat)
        expected = [0, 0, 0, 1]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_with_weights(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0],[0, 0, 0, 1]])
        result = csr_residual(v, mat, [0.5, 0.75])
        expected = [0.0, 0.0, 0.5, 0.25]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_with_weights_csr(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0],[0, 0, 0, 1]])
        result = csr_residual(v, mat, csr_matrix([[0.5], [0.75]]))
        expected = [0.0, 0.0, 0.5, 0.25]
        self.assertListEqual(list(result.toarray()[0]), expected)


class VecDecompositionTests(unittest.TestCase):
    """computing decomposition of a vector into basis vectors"""

    def test_decomp_orthogonal(self):
        """when basis vectors are orthogonal"""
        vT = np.array([4, 4, 0])
        vT.shape = (1, 3)
        BT = np.array([[1, 0, 0], [0, 1, 0]])
        result = vec_decomposition(vT, BT)
        self.assertEqual(result.shape, (2, 1))
        self.assertEqual(result[0, 0], result[1, 0])

    def test_decomp_nonorthogonal(self):
        """when basis vectors are not orthogonal, exact solution possible"""
        vT = np.array([4, 4, 0])
        vT.shape = (1, 3)
        BT = np.array([[5, 1, 0], [1, 5, 0]])
        result = vec_decomposition(vT, BT)
        # structure of output - should have coefficients for two basis vectors
        self.assertEqual(result.shape, (2, 1))
        # this is a symmetrical system, coefficients should be equal
        self.assertAlmostEqual(result[0, 0], result[1, 0])
        # by manual calculation, the coefficients should be 2/3
        self.assertAlmostEqual(result[0,0], 2.0/3)
        self.assertAlmostEqual(result[1,0], 2.0/3)

    def test_decomp_nonorthogonal_2(self):
        """when basis vectors are not orthogonal, exact solution impossible"""
        vT = np.array([4, 4, 0])
        vT.shape = (1, 3)
        BT = np.array([[5, 1, 0], [0, 5, 5]])
        result = vec_decomposition(vT, BT)
        # structure of output - should have coefficients for two basis vectors
        self.assertEqual(result.shape, (2, 1))
        # this is not symmetrical system, coefficients should not be equal
        # and first vector is more relevant than the other
        self.assertGreater(result[0, 0], result[1, 0])

        # compute using a second basis that deviates more from v
        BT2 = np.array([[5, 1, 0], [0, 5, 50]])
        result2 = vec_decomposition(vT, BT2)
        self.assertLess(result2[1, 0], result[1, 0])

    def test_decomp_csr(self):
        """decomposition starting with csr matrices"""
        vT = csr_matrix([4, 4, 0])
        BT = vstack([csr_matrix([5, 1, 0]), csr_matrix([1, 5, 0])])
        result = vec_decomposition(vT.toarray(), BT.toarray())
        # this example mirrors one of the nonorthogonal tests above
        self.assertEqual(result.shape, (2, 1))
        self.assertAlmostEqual(result[0, 0], result[1, 0])
        self.assertAlmostEqual(result[0,0], 2.0/3)
        self.assertAlmostEqual(result[1,0], 2.0/3)

