"""
Handling csr vectors
"""

import numba
from math import sqrt
from pickle import loads, dumps
from scipy.sparse import csr_matrix


def csr_to_bytes(x):
    """Convert a csr vector (one-row matrix) into a bytes-like object

    :param x: csr matrix
    :return: bytes-like object
    """
    return dumps((tuple([float(_) for _ in x.data]),
                  tuple([int(_) for _ in x.indices])))


def bytes_to_csr(x, ncol):
    """convert a bytes object into a csr one-row matrix

    :param x: bytes object
    :param ncol: integer, number of columns in csr matrix
    :return: csr_matrix
    """
    raw = loads(x)
    return csr_matrix((raw[0], raw[1], (0, len(raw[1]))), shape=(1, ncol))


def normalize_csr(a):
    """normalize a csr vector

    Note this performs a normalization in-place,
    i.e. the original vector will change.

    :param a: csr_matrix, assumed a single row vector
    :return: csr_matrix of same size as a, with normalized entries
    """

    n2 = sum([x*x for x in a.data])
    if n2 == 0:
        return a
    a.data *= 1/sqrt(n2)
    return a


def threshold_csr(v, threshold=0.001):
    """set elements in v below a threshold to zero

    :param v: csr vector
    :param threshold: threshold level
    :return: new csr vector with some elements set to zero
    """

    data = []
    indices = []
    for d, i in zip(v.data, v.indices):
        if abs(d) > threshold:
            data.append(d)
            indices.append(i)
    return csr_matrix((data, indices, [0, len(indices)]), shape=v.shape)


@numba.jit
def add_csr(x, data, indices):
    """add csr data to a dense array

    :param x: dense array of floats
    :param data: array of floats
    :param indices: array of integers
    :return: array consisting of x+data
    """
    for i in range(len(indices)):
        x[indices[i]] += data[i]
    return x

