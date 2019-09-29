"""
Handling vectors and vector decompositions
"""

import numba
from math import sqrt
from numpy import matmul
from numpy.linalg import lstsq
from scipy.sparse import csr_matrix


@numba.jit
def vec_norm(a):
    """compute the vector norm of a vector"""
    sum2 = 0
    for i in range(len(a)):
        sum2 += a[i] *a[i]
    return sqrt(sum2)


@numba.jit
def all_zero(a):
    """evaluate if entire vector is made up of zeros"""
    for i in range(len(a)):
        if a[i] != 0.0:
            return 0
    return 1


@numba.jit
def num_nonzero(a):
    """evaluate number of elements in a vector that are nonzero"""
    result = 0
    for i in range(len(a)):
        result += (a[i]!=0.0)
    return result


@numba.jit
def normalize_vec(a):
    """normalize a dense vector"""
    n = vec_norm(a)
    if n == 0:
        return a
    for i in range(len(a)):
        a[i] = a[i]/n
    return a


def normalize_csr(a):
    """normalize a csr vector"""
    n2 = (a.dot(a.transpose())).data[0]
    if n2 == 0:
        return a
    return a.dot(1/sqrt(n2))


@numba.jit
def add_three(a, b, c, wb, wc):
    """add three vectors

    :param a: array
    :param b: array
    :param c: array
    :param wb: real number
    :param wc: real number
    :return: vector a+ wb*b + wc*c
    """

    for i in range(len(a)):
        a[i] += wb*b[i] + wc*c[i]
    return a


def csr_residual(v, mat, weights=None):
    """get the residual of a vector after subtracting other vectors

    :param v: csr matrix with one row
    :param mat: csr matrix with possibly many rows
    :param weights: coefficients for each row in mat, can be in a list,
    otherwise should be in vertical csr_matrix
    :return: a csr matrix with one row, the v-sum (v dot mat) mat
    """
    # avoid work if the matrix indicates no subtraction necessary
    if mat.shape[1] == 0:
        return v.copy()
    # convert weights from a vector into a column vector
    if weights is None:
        weights = [1]*mat.shape[0]
    if type(weights) == list:
        weights = csr_matrix(weights).transpose()
    # perform the dot product and residual
    coeffs = mat.dot(v.transpose())
    components = mat.multiply(coeffs)
    components = components.multiply(weights)
    return csr_matrix(v-components.sum(0))


def vec_decomposition(vT, BT):
    """solves a linear set of equations.

    The underlying model is v = Bx, or v - Bx = 0. This solves for x.

    :param vT: a row vector, the transpose of v
    :param BT: a matrix with basis vector as rows, the transpose of B
    :return: a vector with coefficients
    """

    a = matmul(BT, BT.transpose())
    b = matmul(BT, vT.transpose())
    x, residuals, _, _ = lstsq(a, b, rcond=None)
    return x


def sparse_to_dense(v):
    """convert a one-row sparse matrix into a dense ndarray"""
    return v.toarray()[0]
