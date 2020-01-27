"""
Tests for working with sparse vectors
"""

import numpy as np
import unittest
from numpy import array
from math import sqrt
from scipy.sparse import csr_matrix, vstack
from crossmap.vectors import \
    csr_residual, \
    vec_decomposition, \
    num_nonzero, \
    all_zero, \
    vec_norm, \
    normalize_vec, \
    sign_norm_vec, \
    threshold_vec, \
    ceiling_vec, \
    nonzero_indices, \
    absmax2


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


class VecResidualTests(unittest.TestCase):
    """computing residuals for vector decomposition"""

    def test_residual_from_null_vector(self):
        """starting with a null vector, residuals is non-null"""
        v = csr_matrix([0, 0, 0, 0])
        mat = csr_matrix([0, 1, 0, 0])
        result = csr_residual(v, mat, csr_matrix([1]))
        self.assertListEqual(list(result.toarray()[0]), [0, -1, 0, 0])

    def test_residual_with_zero_weight(self):
        """subtracting nothing return original input"""
        v = csr_matrix([0, 0, 1, 0])
        mat = csr_matrix([0,0,1,0])
        result = csr_residual(v, mat, csr_matrix([0]))
        expected = [0, 0, 1, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null(self):
        """subtracting can lead to a null vector"""
        v = csr_matrix([0, 0, 1, 0])
        mat = csr_matrix([0, 0, 1, 0])
        result = csr_residual(v, mat, csr_matrix([1]))
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null_two_steps(self):
        """subtracting two vectors can eventually lead to a null vector"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0], [0, 0, 0, 1]])
        result = csr_residual(v, mat, csr_matrix([1, 1]).transpose())
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_null_three_steps(self):
        """subtracting two vectors can eventually lead to a null vector"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0], [0, 0, 0, 1], [0, 0, 0, 1]])
        result = csr_residual(v, mat, csr_matrix([1, 0.5, 0.5]).transpose())
        expected = [0, 0, 0, 0]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_to_partial(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([0, 0, 1, 0])
        result = csr_residual(v, mat, csr_matrix([1]))
        expected = [0, 0, 0, 1]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_with_weights(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0], [0, 0, 0, 1]])
        result = csr_residual(v, mat, csr_matrix([0.5, 0.75]).transpose())
        expected = [0.0, 0.0, 0.5, 0.25]
        self.assertListEqual(list(result.toarray()[0]), expected)

    def test_residual_with_weights_csr(self):
        """subtraction of a partial match produce a non-null residual"""
        v = csr_matrix([0, 0, 1, 1])
        mat = csr_matrix([[0, 0, 1, 0],[0, 0, 0, 1]])
        result = csr_residual(v, mat, csr_matrix([[0.5], [0.75]]))
        expected = [0.0, 0.0, 0.5, 0.25]
        self.assertListEqual(list(result.toarray()[0]), expected)


class VectorThresholdingTests(unittest.TestCase):
    """vector thresholding"""

    def test_threshold_vector(self):
        """thresholding of a simple array"""

        a = array([0.4, 1.2, 0.5, 2.8])
        self.assertEqual(sum(a), 4.9)
        result = threshold_vec(a, 1.0)
        self.assertEqual(sum(result), 4.0)

    def test_threshold_with_negatives(self):
        """thresholding of a simple array, keep large negative numbers"""

        a = array([0.4, -2.0, 0.5, 3.5])
        result = threshold_vec(a, 1.0)
        self.assertEqual(sum(result), 1.5)

    def test_ceiling_vector(self):
        """capping values at a ceiling"""

        a = array([0.5, 1.2, 0.2, -2.4, 1.8, 0.8])
        result = ceiling_vec(a, 1.0)
        self.assertEqual(sum(result), 0.5 + 1.0 + 0.2 - 2.4 + 1.0 + 0.8)


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


class VecIndicesTests(unittest.TestCase):
    """Nonzero indices in a vector"""

    v = array([0, 2, 4, 1, 0])

    def test_nonzero_1(self):
        """nonzero index with maximal value"""

        result = nonzero_indices(self.v)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], 2)

    def test_nonzero_zeros(self):
        """nonzero indices from zero vector is empty"""

        result = nonzero_indices(array([0, 0, 0, 0, 0]))
        self.assertEqual(len(result), 0)

    def test_nonzero_2(self):
        """nonzero indices, with a limit"""

        result = nonzero_indices(self.v, 2)
        self.assertEqual(len(result), 2)
        self.assertListEqual(result, [2, 1])

    def test_nonzero_return_nonzero(self):
        """nonzero return only nonzero indices, even when request for more"""

        result = nonzero_indices(self.v, 10)
        self.assertEqual(len(result), 3)


class VecAbsMax2Tests(unittest.TestCase):
    """Searching for values in a vector"""

    def test_absmax2_1a(self):
        """best and runner up in tiny array"""

        result = absmax2(array([2.5]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 2.5)
        self.assertEqual(result[0], 2.5)

    def test_absmax2_1b(self):
        """best and runner up in tiny array"""

        result = absmax2(array([-0.5]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 0.5)
        self.assertEqual(result[0], 0.5)

    def test_absmax2_short(self):
        """best and runner up, with positive and negative elements"""

        result = absmax2(array([-2.5, 1.5]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 2.5)
        self.assertEqual(result[1], 1.5)

    def test_absmax2_long(self):
        """best and runner up, with long input"""

        result = absmax2(array([-2.5, 1.5, 0.2, 3.5, 0.5]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 3.5)
        self.assertEqual(result[1], 2.5)

    def test_absmax2_long2(self):
        """best and runner up, another long input"""

        result = absmax2(array([2.5, 1.5, 0.2, 3.5, 0.5, 4.5]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 4.5)
        self.assertEqual(result[1], 3.5)

    def test_absmax2_ties(self):
        """best and runner up, with ties"""

        result = absmax2(array([2.0, 2.0, 2.0, 3.0, 3.0,
                                4.0, 3.0, 4.0, 2.0, 1.0]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 4.0)
        self.assertEqual(result[1], 3.0)

    def test_absmax2_ties_2(self):
        """best and runner up, with ties, another example"""

        result = absmax2(array([4.0, 4.0, 3.0, 2.0]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 4.0)
        self.assertEqual(result[1], 3.0)

    def test_absmax2_ties_only_max(self):
        """best and runner up, but there is no runner up"""

        result = absmax2(array([1.0, -1.0, -1.0]))
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], 1.0)
        self.assertEqual(result[1], 1.0)


class SignNormTests(unittest.TestCase):
    """Normalization of vectors by sign and length"""

    def test_sign_normalize_positive(self):
        """simple conversion, with normalization of +ve values"""

        a = csr_matrix([1.2, 0.0, 0.2, 0.2, 0, 0, 4.2])
        expected = csr_matrix([0.25, 0, 0.25, 0.25, 0, 0.25])
        a.data = sign_norm_vec(a.data)
        self.assertListEqual(list(a.data), list(expected.data))

    def test_sign_normalize_pos_neg(self):
        """simple conversion, with normalization of +ve and -ve values"""

        a = csr_matrix([2, 3, 0, -1.2, 0,
                        0.2, 0.5, 0, 0, -4.2])
        expected = csr_matrix([0.25, 0.25, 0, -0.5, 0,
                               0.25, 0.25, 0, 0, -0.5])
        a.data = sign_norm_vec(a.data)
        self.assertListEqual(list(a.data), list(expected.data))

    def test_sign_empty_array(self):
        """simple conversion with empty input"""

        a = csr_matrix([0.0, 0.0, 0.0])
        a.data = sign_norm_vec(a.data)
        self.assertEqual(len(a.data), 0)

