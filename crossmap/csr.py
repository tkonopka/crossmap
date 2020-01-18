"""
Handling csr vectors
"""

import numba
from numpy import array
from pickle import loads, dumps
from scipy.sparse import csr_matrix
from .vectors import normalize_vec, absmax2


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
    :return: arrays with data, indices, and a sum of the data
        Note the first two elements are ready to use with csr_matrix.
        The abs max and abs-runner-up are ad-hoc extras.
    """
    raw = loads(x)
    data_max, data_runnerup = 0.0, 0.0
    values, indices = array(raw[0]), array(raw[1])
    if len(raw[0]):
        data_max, data_runnerup = absmax2(values)
    return values, indices, data_max, data_runnerup

    #abs_data = [abs(_) for _ in raw[0]]
    #data_sum = sum(abs_data)
    #data_max = 0.0 if len(abs_data) == 0 else max(abs_data)
    #return array(raw[0]), array(raw[1]), data_sum, data_max


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


def pos_threshold_csr(v, threshold=0.0):
    """set elements in v to positive definitive values

    :param v: csr vector
    :param threshold: threshold level
    :return: new csr vector with some elements set to zero
    """

    data = []
    indices = []
    threshold = max(0, threshold)
    for d, i in zip(v.data, v.indices):
        if d > threshold:
            data.append(d)
            indices.append(i)
    return csr_matrix((data, indices, [0, len(indices)]), shape=v.shape)


def _sign(x):
    """get +1 or -1 value"""
    return +1 if x>0 else -1


def sign_csr(v, normalize=True):
    """set elements in v to +1 or -1 integers

    :param v: csr vector
    :param normalize: logical, if True, output is normalized
    :return: modified csr vector with elements set to integers
    """

    if normalize and len(v.data):
        invlen = 1/len(v.data)
        v.data = array([_sign(_)*invlen for _ in v.data])
    else:
        v.data = array([_sign(_) for _ in v.data])
    return v


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
    :return: array consisting of arr+data
    """
    for i in range(len(indices)):
        arr[indices[i]] += data[i]
    return arr


@numba.jit
def add_sparse_skip(arr, data, indices, skip_index=-1):
    """add sparse data to a dense array

    (Similar to add_sparse, but with an option to skip an index)

    :param arr: dense array of floats
    :param data: array of floats
    :param indices: array of integers
    :param skip_index: integer, skip adding this index
    :return: array consisting of arr+data
    """
    for i in range(len(indices)):
        if indices[i] != skip_index:
            arr[indices[i]] += data[i]
    return arr


@numba.jit
def harmonic_multiply_sparse(factors, data, indices, harmonic_factor):
    """multiply sparse data by a harmonic-mean-scaled factor

    :param factors: dense array of floats
    :param data: array of floats (from a sparse vector)
    :param indices: array of integers (from a sparse vector)
    :param harmonic_factor: float, factor for use with harmonic
        multiplication.
    :return: array consisting of factors*data in sparse format.
        When a harmonic factor is present, the multiplication is by
        (factors*harmonic_factor)/(factors+harmonic_factor)
    """

    for i in range(len(indices)):
        fi = factors[indices[i]]
        data[i] *= (fi * harmonic_factor / (fi + harmonic_factor))
    return data


@numba.jit
def max_multiply_sparse(factors, data, indices, max_factor):
    """multiply sparse data by a factor with upper bound

    :param factors: dense array of floats
    :param data: array of floats (from a sparse vector)
    :param indices: array of integers (from a sparse vector)
    :param max_factor: float, maximal factor forfor use with harmonic
        multiplication.
    :return: array consisting of factors*data in sparse format.
        When max_factor is present, the factors are at most
        equal to the max_factor float
    """

    result = array([0.0]*len(data))
    for i in range(len(indices)):
        result[i] = data[i] * min(max_factor, factors[indices[i]])
    return result
