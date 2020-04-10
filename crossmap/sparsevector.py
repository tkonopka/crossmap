"""
Handling sparse data using dicts

This class encode sparse vectors as a dictionary. The objective
is to have decent space efficiency and allow quicker addition than csr_matrix.
"""

from scipy.sparse import csr_matrix


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
        :return: self to allow concatenating command
        """

        return self.add(v.indices, v.data, multiplier)

    def add_dense(self, v, multiplier=1.0):
        """add a dense vector

        :param v: array or list
        :param multiplier: numeric, multiplier for values in v
        :return: self to allow concatentating command
        """

        data = self.data
        for i in range(len(v)):
            d = v[i]
            if d == 0.0:
                continue
            if i not in data:
                data[i] = 0.0
            data[i] += d*multiplier
        return self

    def add(self, indices, values, multiplier=1.0):
        """add a small set of sparse data to this object

        :param indices: list of indices (integers)
        :param values: list of numeric values to match indices
        :param multiplier: numeric, multiplier for values in data
        :return: self to allow concatenating command
        """

        data = self.data
        for i, d in zip(indices, values):
            if i not in data:
                data[i] = 0.0
            data[i] += d*multiplier
        return self

    def to_csr(self, n, threshold=None):
        """create a csr vector representation of the dictionary

        :param n: dimension of the output object
        :param threshold: real number, only entries greater in absolute value
            are preserved in the output
        :return: csr_matrix object
        """

        indices, data = [], []
        if threshold is None or threshold == 0.0:
            for i, d in self.data.items():
                indices.append(i)
                data.append(d)
        else:
            if len(self.data):
                threshold *= max(self.data.values())
            for i, d in self.data.items():
                if abs(d) > threshold:
                    indices.append(i)
                    data.append(d)
        return csr_matrix((data, indices, (0, len(data))), shape=(1, n))

    def __str__(self):
        return str(self.data)
