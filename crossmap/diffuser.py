"""
Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features. The way in which
the diffusion spreads is controlled via connections store in a db.
"""

from logging import info, warning, error
from scipy.sparse import csr_matrix
from numpy import array
from .db import CrossmapDB
from .encoder import CrossmapEncoder
from .tokens import CrossmapTokenizer
from .csr import normalize_csr, threshold_csr, sign_csr
from .csr import add_sparse, harmonic_multiply_sparse
from .sparsevector import Sparsevector
from .vectors import sparse_to_dense


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
            self.db = CrossmapDB(settings.db_file())
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
        self.tokenizer = CrossmapTokenizer(self.settings)
        self.encoder = CrossmapEncoder(self.feature_map, self.tokenizer)
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
            v = sign_csr(v, normalize=True)
            total += 1
            for i, d in zip(v.indices, v.data):
                result[i].add_csr(v, _sign(d))
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

        threshold = self.threshold
        for row in self.db.get_data(dataset, idxs=data_idxs):
            v = row["data"]
            if threshold > 0:
                v = threshold_csr(v, threshold)
            v = sign_csr(v, normalize=True)
            v_indices = [int(_) for _ in v.indices]
            if len(v.indices) == 0:
                continue

            v_dict = {i: d for i, d in zip(v_indices, v.data)}
            counts = self.db.get_counts(dataset, v_indices)
            for k in list(counts.keys()):
                d = v_dict[k]
                counts[k] += v * _sign(d)
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
                    # ddata[0] contains values from a sparse vector
                    # ddata[1] contains indexes matched to the values in ddata[0]
                    # ddata[2] contains a sum of all data entries in the vector
                    # ddata[3] contains the maximal value
                    if ddata[3] == 0.0:
                        continue
                    row_sum = ddata[2]
                    data = hms(f_weights, ddata[0], ddata[1], f_weights[di])
                    multiplier = min(1.0, (w_dense[di]/v_dense[di]))
                    multiplier *= last_result[di] / row_sum
                    data *= pass_weight * value * multiplier
                    # add the diffusion parts (but not to self)
                    result = add_sparse(result, data, ddata[1], di)
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


def _sign(x):
    """get the sign of a number"""
    return 1 if x >= 0 else -1

