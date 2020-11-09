"""
Handling vectors and vector decompositions
"""

import numba
from math import sqrt
from numpy import matmul
from numpy.linalg import lstsq


@numba.jit
def vec_norm(a):
    """compute the vector norm of a vector"""
    sum2 = 0
    for i in range(len(a)):
        sum2 += a[i] * a[i]
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
    """normalize a dense vector

    Note this performs a normalization in-place, i.e.
    the original vector will change

    :param a: dense vector, as an array or list
    :return: vector with normalized entries
    """
    n = vec_norm(a)
    if n == 0:
        return a
    inv_norm = 1/n
    for i in range(len(a)):
        a[i] *= inv_norm
    return a


@numba.jit
def sign_norm_vec(a):
    """custom normalization of a dense vector by sign and length

    Note this performs a normalization in-place, i.e.
    the original vector will change

    :param a: dense vector, as an array or list
    :return: modified vector with equalized elements.
        In particular, positive elements are set all equal
        and negative elements are set all equal. When length_norm
        is activated, the sum of positives sum to 1 and the sum
        of negatives sum to -1.
    """
    norm_pos, norm_neg = 0.0, 0.0
    for _ in range(len(a)):
        if a[_] > 0:
            norm_pos += 1
        elif a[_] < 0:
            norm_neg += 1
    if norm_pos > 0:
        norm_pos = 1.0 / norm_pos
    if norm_neg > 0:
        norm_neg = -1.0 / norm_neg
    for _ in range(len(a)):
        if a[_] > 0:
            a[_] = norm_pos
        elif a[_] < 0:
            a[_] = norm_neg
    return a


@numba.jit
def ceiling_vec(a, c):
    """ensure that values in a vector are below a ceiling

    Note this performs an operation in-place, i.e.
    the original vector will change

    :param a: vector, as an array or list
    :return: vector with some modified values
    """

    for i in range(len(a)):
        if a[i] > c:
            a[i] = c
    return a


@numba.jit
def cap_vec(a, cap):
    """ensure that values in a vector are capped from above and below

    Note this performs an operation in-place, i.e.
    the original vector will change

    :param a: vector, as an array or list
    :param cap: numeric value for range [-cap, cap]
    :return: vector with some modified values
    """

    for i in range(len(a)):
        a[i] = min(cap, max(-cap, a[i]))
    return a


@numba.jit
def add_three(a, b, c, wb, wc):
    """add three vectors with weights

    Note this modifies the input vector a.

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


@numba.jit
def absmax2(a):
    """find the maximal and runner-up values in an array

    :param a: array of numbers
    :return: array of length 2, values of maximal and runner-up absolute values
    """

    result = [-1.0, -1.0]
    for i in range(len(a)):
        v = abs(a[i])
        if v > result[0]:
            result[1] = result[0]
            result[0] = v
        elif result[0] > v > result[1]:
            result[1] = v
    if result[1] < 0:
        result[1] = result[0]
    return result


def csr_residual(v_t, b_t, weights):
    """get the residual of a vector after subtracting other vectors

    :param v_t: csr matrix with one row
    :param b_t: csr matrix with possibly many rows
    :param weights: coefficients for each row in mat in vertical csr_matrix
    :return: a csr matrix with one row, the v-sum (v dot mat) mat
    """
    # an alternative implementation is
    # v_t - weights.transpose().dot(b_t)
    # but in practice the implementation below seems faster in cProfile

    # compute the modeled vector using b*w
    model = (b_t.transpose()).dot(weights)
    return v_t - model.transpose()


@numba.jit
def threshold_vec(v, threshold=0.001):
    """set elements in array v below a threshold to zero

    :param v: array vector
    :param threshold: threshold level
    :return: array with elements smaller than threshold set to zero
    """
    for i in range(len(v)):
        if abs(v[i]) < threshold:
            v[i] = 0
    return v


def vec_decomposition(v_t, b_t):
    """solves a linear set of equations.

    The underlying model is v = Bx, or v - Bx = 0. This solves for x.

    :param v_t: a row vector, the transpose of v
    :param b_t: a matrix with basis vector as rows, the transpose of B
    :return: a vector with coefficients
    """
    a = matmul(b_t, b_t.transpose())
    b = matmul(b_t, v_t.transpose())
    x, residuals, _, _ = lstsq(a, b, rcond=None)
    return x


def sparse_to_dense(v):
    """convert a one-row sparse matrix into a dense ndarray"""
    return v.toarray()[0]


def nonzero_indices(arr, max_number=1):
    """get an array of indices that have nonzero value"""
    result = []
    for i in range(len(arr)):
        if arr[i] != 0.0:
            result.append((arr[i], i))
    result = sorted(result, reverse=True)
    n = min(max_number, len(result))
    return [result[_][1] for _ in range(n)]

