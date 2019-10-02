"""
Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features.
"""

from logging import info, error
from scipy.sparse import csr_matrix
from .db import CrossmapDB
from .tokens import CrossmapTokenizer
from .encoder import CrossmapEncoder
from .vectors import normalize_csr


class CrossmapDiffuser:
    """Vector diffusion for crossmap"""

    def __init__(self, settings):
        """initialize an instance with a connection to a database

        :param settings:  CrossmapSettings object
        """

        self.settings = settings
        self.db = CrossmapDB(settings.db_file())
        self.db.build()
        self.feature_map = self.db.get_feature_map()
        if len(self.feature_map) == 0:
            error("feature map is empty")

    def _build_counts(self, files, label=""):
        """scan files to generate a counts table"""

        info("Building diffusion index for " + label)
        fm = self.feature_map
        nf = len(fm)
        tokenizer = CrossmapTokenizer(self.settings)
        encoder = CrossmapEncoder(fm, tokenizer)
        result = [csr_matrix([0]*len(fm)) for _ in range(nf)]
        for _tokens, _id, _title in encoder.documents(files):
            for i in _tokens.indices:
                result[i] += _tokens

        self.db.set_counts(label, result)

    def build(self):
        """populate count tables based on all data files"""

        settings = self.settings
        for label in self.settings.data_files.keys():
            if label not in self.db.datasets:
                self.db.register_dataset(label)
        for label, filepath in settings.data_files.items():
            self._build_counts(filepath, label)

    def diffuse(self, v, strength, normalize=True):
        """create a new vector by diffusing values

        :param v: csr vector
        :param strength: dict, diffusion strength from each dataset
        :param normalize: logical, ensures final vector has unit norm
        :return: csr vector
        """

        result = v.copy()
        v_indexes = [int(_) for _ in v.indices]
        v_data = {v.indices[_]: v.data[_] for _ in range(len(v.data))}
        for corpus, value in strength.items():
            diffusion_data = self.db.get_counts(corpus, v_indexes)
            for di, ddata in diffusion_data.items():
                if ddata.sum() == 0:
                    continue
                ddata[0, di] = 1
                vnorm = abs(ddata.sum())
                result += ddata.dot(v_data[di]*value/vnorm)
        if normalize:
            result = normalize_csr(result)
        return result

