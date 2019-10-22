"""
Handling csr vectors
"""

import numba
from numpy import array
from pickle import loads, dumps
from scipy.sparse import csr_matrix
from .vectors import normalize_vec


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


def bytes_to_arrays(x):
    """convert a bytes object into a pair of arrays

    :param x: bytes object
    :param ncol: integer, number of columns in csr matrix
    :return: arrays with data, indices, and a sum of the data
        Note the first two elements are ready to use with csr_matrix,
        but the sum of the data is an ad-hoc extra.
    """
    raw = loads(x)
    data_sum = sum([abs(_) for _ in raw[0]])
    return array(raw[0]), array(raw[1]), data_sum


def normalize_csr(v):
    """normalize a csr vector

    Note this performs a normalization in-place,
    i.e. the original vector will change.

    :param v: csr_matrix, assumed a single row vector
    :return: csr_matrix of same size as a, with normalized entries
    """

    v.data = normalize_vec(v.data)
    return v


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


def dimcollapse_csr(v, indexes=(), normalize=True):
    """dimensional collapse of a vector

    :param v: csr vector
    :param indexes: allowed dimensional indexes
    :param normalize: logical, set True to rescale values to unit norm
    :return: new csr vector, values outside indexes reset to zero
    """

    data = []
    indices = []
    for d, i in zip(v.data, v.indices):
        if i in indexes:
            data.append(d)
            indices.append(i)
    if normalize:
        data = normalize_vec(array(data))
    result = csr_matrix((data, indices, [0, len(indices)]), shape=v.shape)
    return result


@numba.jit
def add_sparse(arr, data, indices):
    """add sparse data to a dense array

    :param arr: dense array of floats
    :param data: array of floats
    :param indices: array of integers
    :return: array consisting of x+data
    """
    for i in range(len(indices)):
        arr[indices[i]] += data[i]
    return arr

