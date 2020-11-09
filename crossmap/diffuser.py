"""
Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features. The way in which
the diffusion spreads is controlled via connections stored in a db.
"""

from logging import info, warning, error
from math import sqrt
from numpy import array
from .dbmongo import CrossmapMongoDB as CrossmapDB
from .csr import FastCsrMatrix, normalize_csr, threshold_csr
from .csr import harmonic_multiply_sparse, diffuse_sparse, get_value_csr
from .sparsevector import Sparsevector
from .vectors import sparse_to_dense, sign_norm_vec, cap_vec


def weights_arr(feature_map):
    """create an array of weights from a feature dict"""
    result = array([0.0]*len(feature_map))
    for _, v in feature_map.items():
        result[v[0]] = v[1]
    return result


class CrossmapDiffuser:
    """Vector diffusion for crossmap"""

    def __init__(self, settings, db=None):
        """initialize an instance with a connection to a database

        :param settings:  CrossmapSettings object
        :param db: CrossmapDB object, a new db connection will be made if None
        """

        self.settings = settings
        self.threshold = self.settings.diffusion.threshold
        self.db = db if db is not None else CrossmapDB(settings)
        self.feature_map = self.db.get_feature_map()
        if len(self.feature_map) == 0:
            error("feature map is empty")
        self.feature_weights = weights_arr(self.feature_map)
        self.num_passes = settings.diffusion.num_passes

    def _set_empty_counts(self, dataset):
        """set up empty co-occurance records for a dataset

        :param dataset: string, identifier for dataset in db
        """

        num_rows = self.db.count_rows(dataset, "counts")
        if num_rows > 0:
            warning("Resetting diffusion index: " + dataset)
        info("Setting empty diffusion index: " + dataset)
        nf = len(self.feature_map)
        empty = FastCsrMatrix(([], [], [0, 0]), shape=(1, nf))
        result = [empty for _ in range(nf)]
        self.db.set_counts(dataset, result)

    def _build_counts(self, dataset):
        """construct co-occurrence records for one dataset

        :param dataset: string, identifier for dataset in db
        """

        num_rows = self.db.count_rows(dataset, "counts")
        if num_rows > 0:
            msg = "Skipping build of diffusion index: " + dataset
            warning(msg + " - already exists")
            return
        info("Building diffusion index: " + dataset)
        threshold = self.threshold
        progress, total = self.settings.logging.progress, 0
        fm = self.feature_map
        nf = len(fm)
        result = [Sparsevector() for _ in range(nf)]
        for row in self.db.all_data(dataset):
            total += 1
            v = row["data"]
            if threshold > 0:
                v = threshold_csr(v, threshold)
            v_pos, v_indices = sign_norm_vec(v.data), v.indices
            v_neg = -v_pos
            for i, d in zip(v_indices, v_pos):
                if d > 0:
                    result[i].add(v_indices, v_pos)
                else:
                    result[i].add(v_indices, v_neg)
            if total % progress == 0:
                info("Progress: " + str(total))
        # replace dictionaries by csr_matrix (in place to save memory)
        for _ in range(nf):
            result[_] = result[_].to_csr(nf, threshold / 10)
        self.db.set_counts(dataset, result)

    def build(self):
        """populate count tables based on all data files"""

        for label in self.settings.data.collections.keys():
            if label not in self.db.datasets:
                self.db.register_dataset(label)
            self._build_counts(label)

    def update(self, dataset, data_idxs=()):
        """augment counts based on vectors from the data table

        :param dataset: string, dataset identifier
        :param data_idxs: list of integer indexes in the data table
        """

        # if this is a first update, need to seed the counts table
        num_rows = self.db.count_rows(dataset, "counts")
        if num_rows == 0:
            self._set_empty_counts(dataset)

        for row in self.db.get_data(dataset, idxs=data_idxs):
            v = row["data"]
            if len(v.indices) == 0:
                continue
            v.data = sign_norm_vec(v.data)
            v_indices = [int(_) for _ in v.indices]
            counts = self.db.get_counts(dataset, v_indices)
            for i, d in zip(v_indices, v.data):
                if d > 0:
                    counts[i] += v
                else:
                    counts[i] -= v
            self.db.update_counts(dataset, counts)

    def diffuse(self, v, strength):
        """create a new vector by diffusing values

        :param v: csr vector
        :param strength: dict, diffusion strength from each dataset
        :return: csr vector
        """

        if len(v.data) == 0:
            return v

        num_passes = self.num_passes
        weights = self.feature_weights
        strength = _nonzero_strength(strength)
        result = sparse_to_dense(v)

        # fetch counts data from db, then re-use in multiple passes
        v_indexes = [int(_) for _ in v.indices]
        counts = dict()
        hms = harmonic_multiply_sparse
        for dataset in strength.keys():
            temp = self.db.get_counts_arrays(dataset, v_indexes)
            dataset_dict = dict()
            for i, data in temp.items():
                iv = get_value_csr(data[0], data[1], i)
                norm = sqrt(iv)
                adjusted = cap_vec(data[0], norm)
                adjusted = hms(weights, adjusted, data[1], weights[i])
                dataset_dict[i] = [adjusted, data[1], norm]
            counts[dataset] = dataset_dict

        for pass_w in _pass_weights(num_passes):
            last_result = result.copy()
            for dataset, corpus_w in strength.items():
                corpus_data = counts[dataset]
                for i, idata in corpus_data.items():
                    if idata[2] == 0.0:
                        continue
                    data = idata[0] * pass_w * corpus_w / idata[2]
                    indices = idata[1]
                    diffuse_sparse(result, last_result, i, data, indices)

        # cut feature with very low weights
        val_min = min(abs(v.data))
        result = normalize_csr(FastCsrMatrix(result))
        return normalize_csr(threshold_csr(result, val_min/50))


def _pass_weights(tot):
    """compute a weight for a diffusion pass using 1/p!

    :param tot: total number of passes
    :return: real number
    """

    result = array([1.0]*tot)
    for i in range(1, tot):
        result[i] = (i + 1) * result[i]
    result = [1/_ for _ in result]
    return result / sum(result)


def _nonzero_strength(x):
    """make sure a dictionary has only nonzero values"""

    for k in list(x.keys()):
        if x[k] == 0:
            x.pop(k)
    return x

