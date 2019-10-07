"""
Functions handling csr vectors
"""

from pickle import loads, dumps
from scipy.sparse import csr_matrix


def csr_to_bytes(x):
    """Convert a csr row vector into a bytes-like object

    :param x: csr matrix
    :return: bytes-like object
    """
    result = (tuple([float(_) for _ in x.data]),
              tuple([int(_) for _ in x.indices]),
              tuple([int(_) for _ in x.indptr]))
    return dumps(result)


def bytes_to_csr(x, ncol):
    """convert a bytes object into a csr row matrix

    :param x: bytes object
    :param ncol: integer, number of columns in csr matrix
    :return: csr_matrix
    """
    return csr_matrix(loads(x), shape=(1, ncol))

