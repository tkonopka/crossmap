"""
Handling sparse data using dicts

This class encode sparse vectors as a dictionary. The objective
is to have decent space efficiency and allow quicker addition than csr_matrix.
"""

from numpy import array, int32, float64
from .csr import threshold_csr_arrays, csr_vector


class Sparsevector:

    def __init__(self, v=None):
        """initialize as an empty dictionary, or copy from a vector

        :param v: csr_vector as baseline
        """

        data = dict()
        if v is not None:
            for i, d in zip(v.indices, v.data):
                data[i] = d
        self.data = data

    def add_csr(self, v, multiplier=1.0):
        """add a csr vector

        :param v: csr vector
        :param multiplier: numeric, multiplier for values in v
        """

        self.add(v.indices, v.data*multiplier)

    def add_dense(self, v, multiplier=1.0):
        """add a dense vector

        :param v: array or list
        :param multiplier: numeric, multiplier for values in v
        """

        data = self.data
        for i in range(len(v)):
            d = v[i]
            if d == 0.0:
                continue
            if i not in data:
                data[i] = 0.0
            data[i] += d * multiplier

    def add(self, indices, values):
        """add a small set of sparse data to this object

        :param indices: list of indices (integers)
        :param values: list of numeric values to match indices
        :param multiplier: numeric, multiplier for values in data
        """

        data = self.data
        for i, d in zip(indices, values):
            try:
                data[i] += d
            except KeyError:
                data[i] = d

    def to_csr(self, n, threshold=None):
        """create a csr vector representation of the dictionary

        :param n: dimension of the output object
        :param threshold: real number, only entries greater in absolute value
            are preserved in the output
        :return: csr_matrix object
        """

        _data = self.data
        indices = array(list(_data.keys()), dtype=int32, copy=False)
        data = array([_data[_] for _ in indices], dtype=float64, copy=False)
        if len(data) and threshold is not None and threshold != 0.0:
            threshold *= max(data)
            data, indices = threshold_csr_arrays(data, indices, threshold)
        return csr_vector(data, indices, n)

    def __str__(self):
        return str(self.data)

