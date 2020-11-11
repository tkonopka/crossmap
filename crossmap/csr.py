"""
Handling csr vectors
"""

import numba
from numpy import array, int32, float64
from pickle import loads, dumps
from scipy.sparse import csr_matrix
from .vectors import normalize_vec


class FastCsrMatrix(csr_matrix):
    """a modified csr_matrix class that does not perform checks"""

    def check_format(self, full_check=True):
        pass


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
    return FastCsrMatrix((raw[0], raw[1], (0, len(raw[1]))), shape=(1, ncol))


def bytes_to_arrays(x):
    """convert a bytes object into a pair of arrays

    :param x: bytes object
    :return: arrays with data, indices, and a sum of the data
        Note the first two elements are ready to use with csr_matrix.
        The abs max and abs-runner-up are ad-hoc extras.
    """
    raw = loads(x)
    values = array(raw[0], dtype=float64, copy=False)
    indices = array(raw[1], dtype=int32, copy=False)
    return values, indices


def normalize_csr(v):
    """normalize a csr vector

    Note this performs a normalization in-place,
    i.e. the original vector will change.

    :param v: csr_matrix, assumed a single row vector
    :return: csr_matrix of same size as a, with normalized entries
    """

    v.data = normalize_vec(v.data)
    return v


@numba.jit
def threshold_csr_arrays(data, indices, threshold):
    """helper to threshold_csr"""
    result_data, result_indices = [], []
    for i in range(len(data)):
        d = data[i]
        if abs(d) > threshold:
            result_data.append(d)
            result_indices.append(indices[i])
    return result_data, result_indices


def csr_vector(data, indices, n):
    """create a csr_matrix with only one row, i.e. a vector"""
    result = FastCsrMatrix(([], [], (0, 0)), shape=(1, n))
    result.data = array(data, dtype=float64, copy=False)
    result.indices = array(indices, dtype=int32, copy=False)
    result.indptr = array([0, len(indices)], dtype=int32, copy=False)
    return result


def threshold_csr(v, threshold=0.001):
    """set elements in v below a threshold to zero

    :param v: csr vector
    :param threshold: threshold level
    :return: new csr vector with some elements set to zero
    """

    data, indices = threshold_csr_arrays(v.data, v.indices, threshold)
    return csr_vector(data, indices, v.shape[1])


@numba.jit
def _pos_neg_csr_arrays(data, indices):
    """helper to split a data vector into positive and negative components"""
    pos_data, neg_data = [], []
    pos_indices, neg_indices = [], []
    for i in range(len(data)):
        d = data[i]
        if d > 0:
            pos_data.append(d)
            pos_indices.append(indices[i])
        elif d < 0:
            neg_data.append(d)
            neg_indices.append(indices[i])
    return pos_data, pos_indices, neg_data, neg_indices


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
    result = FastCsrMatrix((data, indices, [0, len(indices)]), shape=v.shape)
    return result


@numba.jit
def get_value_csr(data, indices, index):
    """get one value from a sparse vector"""
    for i in range(len(indices)):
        if indices[i] == index:
            return data[i]
    return 0.0


@numba.jit
def diffuse_sparse(arr, concentrations, origin_index, data, indices):
    """add sparse data to a dense array with a gradient add

    :param arr: dense array of floats
    :param concentrations: dense array of concentrations
    :param origin_index: index in concentrations for the source of diffusion
    :param data: array of floats with diffusion magnitudes
    :param indices: array of integers for destination of diffusion
    :return: array consisting of arr+magnitude*(delta concentration)
    """
    c0 = concentrations[origin_index]
    if c0 > 0:
        for i in range(len(indices)):
            index = indices[i]
            diff = c0-concentrations[index]
            if diff > 0:
                arr[index] += data[i] * diff
                arr[index] = min(c0, arr[index])
    else:
        for i in range(len(indices)):
            index = indices[i]
            diff = c0-concentrations[index]
            if diff < 0:
                arr[index] += data[i] * diff
                arr[index] = max(c0, arr[index])


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
    :param data: dense array of floats (from a sparse vector)
    :param indices: array of integers (from a sparse vector)
    :param harmonic_factor: float, factor for use with harmonic
        multiplication.
    :return: array consisting of factors*data in sparse format.
        When a harmonic factor is present, the multiplication is by
        (factors)/(factors+harmonic_factor)
    """

    for i in range(len(indices)):
        fi = factors[indices[i]]
        data[i] *= fi / (fi + harmonic_factor)
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


@numba.jit
def csr_data_indices(arr):
    """extract data and indices arrays from a dense vector

    (this may seem like it may be done faster with np.array.nonzero
    and similar tools, but this implementation is faster)

    :param arr: dense array
    :return: arrays with nonzero data elements, and corresponding indices
    """

    data, indices = [], []
    for i in range(len(arr)):
        if arr[i] != 0.0:
            data.append(arr[i])
            indices.append(i)
    return data, indices

