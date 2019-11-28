"""
Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features. The way in which
the diffusion spreads is controlled via connections store in a db.
"""

from logging import info, warning, error
from scipy.sparse import csr_matrix
from .db import CrossmapDB
from .csr import normalize_csr, threshold_csr, add_sparse
from .vectors import threshold_vec


def sign(x):
    """get the sign of a number"""
    result = 1 if x >= 0 else -1
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
        if db is None:
            self.db = CrossmapDB(settings.db_file())
            self.db.build()
        else:
            self.db = db
        self.feature_map = self.db.get_feature_map()
        if len(self.feature_map) == 0:
            error("feature map is empty")

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

        :param dataset: string, identifier for dataset in db
        """

        # check existing state of counts table
        num_rows = self.db.count_rows(dataset, "counts")
        if num_rows > 0:
            msg = "Skipping build of diffusion index for " + dataset
            warning(msg + " - already exists")
            return

        info("Building diffusion index for " + dataset)
        threshold = self.threshold
        progress = self.settings.logging.progress
        fm = self.feature_map
        nf = len(fm)
        empty = csr_matrix([0.0]*len(fm))
        result = [empty.copy() for _ in range(nf)]
        total = 0
        for row in self.db.all_data(dataset):
            v = row["data"]
            if threshold > 0:
                v = threshold_csr(v, threshold)
            v_max = max(v.data)
            total += 1
            for i, d in zip(v.indices, v.data):
                result[int(i)] += v*(d/v_max)
            if total % progress == 0:
                info("Progress: " + str(total))
        self.db.set_counts(dataset, result)

    def build(self):
        """populate count tables based on all data files"""

        settings = self.settings
        for label in self.settings.data_files.keys():
            if label not in self.db.datasets:
                self.db.register_dataset(label)
        for label, filepath in settings.data_files.items():
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
            v_indices = [int(_) for _ in v.indices]
            if len(v.indices) == 0:
                continue
            v_max = max(v.data)

            # update features with positive weights
            v_dict = {i: d for i, d in zip(v_indices, v.data)}
            counts = self.db.get_counts(dataset, v_indices)
            for k in list(counts.keys()):
                d = v_dict[k]
                counts[k] += v*(d/v_max)
            self.db.update_counts(dataset, counts)

    def diffuse(self, v, strength, normalize=True, threshold=0):
        """create a new vector by diffusing values

        :param v: csr vector
        :param strength: dict, diffusion strength from each dataset
        :param normalize: logical, ensures final vector has unit norm
        :return: csr vector
        """

        # this function involves adding many csr vectors together
        # empirical tests show that it is faster to keep "result"
        # as dense array and add into it, rather than keep it sparse
        # and have its structure change many times
        result = v.toarray()[0]
        v_indexes = [int(_) for _ in v.indices]
        v_data = {v.indices[_]: v.data[_] for _ in range(len(v.data))}
        for corpus, value in strength.items():
            diffusion_data = self.db.get_counts_arrays(corpus, v_indexes)
            for di, ddata in diffusion_data.items():
                # ddata[2] contains a sum of all data entries in the vector
                # ddata[3] contains the maximal value
                row_normalization = ddata[3]
                if row_normalization == 0.0:
                    continue
                data = ddata[0]
                if threshold > 0:
                    data = threshold_vec(data, threshold*row_normalization)
                data *= v_data[di]*value/row_normalization
                result = add_sparse(result, data, ddata[1])
        result = csr_matrix(result)
        if normalize:
            result = normalize_csr(result)
        return result
