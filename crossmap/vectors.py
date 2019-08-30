"""
Handling vectors and vector decompositions
"""

from numpy import matmul
from numpy.linalg import lstsq
from scipy.sparse import csr_matrix


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
