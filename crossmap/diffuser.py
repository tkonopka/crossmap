"""
Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features. The way in which
the diffusion spreads is controlled via connections stored in a db.
"""

from logging import info, warning, error
from scipy.sparse import csr_matrix
from numpy import array, sign
#from .dbsqlite import CrossmapSqliteDB as CrossmapDB
from .dbmongo import CrossmapMongoDB as CrossmapDB
from .csr import normalize_csr, threshold_csr
from .csr import add_sparse, harmonic_multiply_sparse
from .sparsevector import Sparsevector
from .vectors import sparse_to_dense, ceiling_vec, sign_norm_vec


class CrossmapDiffuser:
    """Vector diffusion for crossmap"""

    def __init__(self, settings, db=None):
        """initialize an instance with a connection to a database

        :param settings:  CrossmapSettings object
        :param db: CrossmapDB object, a new db connection will be made if None
        """

        self.settings = settings
        self.threshold = self.settings.diffusion.threshold
        if db is None:
            self.db = CrossmapDB(settings)
            self.db.build()
        else:
            self.db = db
        self.feature_map = self.db.get_feature_map()
        if len(self.feature_map) == 0:
            error("feature map is empty")
        weights = array([0.0]*len(self.feature_map))
        for _, v in self.feature_map.items():
            weights[v[0]] = v[1]
        self.feature_weights = weights / weights.mean()
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
        empty = csr_matrix([0.0]*nf)
        result = [empty.copy() for _ in range(nf)]
        self.db.set_counts(dataset, result)

    def _build_counts(self, dataset=""):
        """construct co-occurrence records for one dataset

        (This version uses building from database)

        :param dataset: string, identifier for dataset in db
        """

        # check existing state of counts table
        num_rows = self.db.count_rows(dataset, "counts")
        if num_rows > 0:
            msg = "Skipping build of diffusion index: " + dataset
            warning(msg + " - already exists")
            return

        info("Building diffusion index: " + dataset)
        threshold = self.threshold
        progress = self.settings.logging.progress
        fm = self.feature_map
        nf = len(fm)
        result = [Sparsevector() for _ in range(nf)]
        total = 0
        for row in self.db.all_data(dataset):
            v = row["data"]
            if threshold > 0:
                v = threshold_csr(v, threshold)
            v.data = sign_norm_vec(v.data)
            total += 1
            for i, d in zip(v.indices, v.data):
                result[i].add_csr(v, sign(d))
            if total % progress == 0:
                info("Progress: " + str(total))
        # replace dictionaries by csr_matrix (in place to save memory)
        for _ in range(nf):
            result[_] = result[_].to_csr(nf)
        self.db.set_counts(dataset, result)

    def build(self):
        """populate count tables based on all data files"""

        for label in self.settings.data_files.keys():
            if label not in self.db.datasets:
                self.db.register_dataset(label)
            self._build_counts(label)

    def update(self, dataset, data_idxs=[]):
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
            v.data = sign_norm_vec(v.data)
            v_indices = [int(_) for _ in v.indices]
            if len(v.indices) == 0:
                continue
            v_dict = {i: d for i, d in zip(v_indices, v.data)}
            counts = self.db.get_counts(dataset, v_indices)
            for k in list(counts.keys()):
                d = v_dict[k]
                counts[k] += v * sign(d)
            self.db.update_counts(dataset, counts)

    def diffuse(self, v, strength, weight=None):
        """create a new vector by diffusing values

        :param v: csr vector
        :param strength: dict, diffusion strength from each dataset
        :param weight: csr vector with weights for each feature for diffusion.
            Algorithm uses v if weight is unspecified, but this can give too
            much emphasis to features that represent overlapping kmers from
            long words.
        :return: csr vector
        """

        strength = _nonzero_strength(strength)
        v_dense = sparse_to_dense(v)
        if weight is not None:
            w_dense = sparse_to_dense(weight)
        else:
            w_dense = v_dense
        result = sparse_to_dense(v)

        # fetch counts data from db, then re-use in multiple passes
        v_indexes = [int(_) for _ in v.indices]
        counts = dict()
        for corpus in strength.keys():
            counts[corpus] = self.db.get_counts_arrays(corpus, v_indexes)

        num_passes = self.num_passes
        f_weights = self.feature_weights
        hms = harmonic_multiply_sparse
        for pass_weight in _pass_weights(num_passes):
            last_result = result.copy()
            for corpus, value in strength.items():
                diffusion_data = counts[corpus]
                for di, ddata in diffusion_data.items():
                    # ddata[0] - values from a sparse vector
                    # ddata[1] - indexes matched to the values in ddata[0]
                    # ddata[2] - a maximal value in values
                    # ddata[3] - a runner-up
                    row_norm = ddata[3]
                    if row_norm == 0.0:
                        continue
                    # cap by row_norm (avoids over-diffusing into self)
                    data = ceiling_vec(ddata[0].copy(), row_norm)
                    # avoid diffusion from important feature to inflate value
                    # of an unimportant feature
                    data = hms(f_weights, data, ddata[1], f_weights[di])
                    # penalize diffusion from overlapping tokens
                    # multiplier = min(1.0, (w_dense[di]/v_dense[di]))
                    multiplier = w_dense[di]/v_dense[di]
                    multiplier *= last_result[di] / row_norm
                    data *= pass_weight * value * multiplier
                    result = add_sparse(result, data, ddata[1])
        return normalize_csr(csr_matrix(result))


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

