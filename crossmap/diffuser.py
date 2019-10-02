"""Diffuser for crossmap vectors

The diffuser is a class that can take a vector and diffuse
values for certain features into other features.
"""

from logging import error
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
        fm = self.feature_map
        tokenizer = CrossmapTokenizer(self.settings)
        encoder = CrossmapEncoder(fm, tokenizer)

        # ensure to start from scratch
        self.db._clear_table("counts_"+label)

        result = [csr_matrix([0]*len(fm)) for _ in range(len(fm))]
        for _tokens, _id, _title in encoder.documents(files):
            for i in _tokens.indices:
                result[i] += _tokens

        self.db._set_counts(result, tab=label)

    def build(self):
        """populate count tables based on all data files"""
        settings = self.settings
        self._build_counts(settings.data_files["targets"], "targets")
        self._build_counts(settings.data_files["documents"], "documents")
        self.db.count_features()

    def diffuse(self, v, strength=None, normalize=True):
        """create a new vector by diffusing values

        :param v: csr vector
        :param strength: diffusion strength
        :param normalize: logical, ensures final vector has unit norm
        :return: csr vector
        """

        if strength is None:
            strength = dict(targets=1, documents=1)

        result = v.copy()
        v_indexes = [int(_) for _ in v.indices]
        v_data = {v.indices[_]: v.data[_] for _ in range(len(v.data))}
        for corpus, value in strength.items():
            diffusion_data = self.db._get_counts(v_indexes, table=corpus)
            for di, ddata in diffusion_data.items():
                if ddata.sum() == 0:
                    continue
                ddata[0, di] = 1
                vnorm = abs(ddata.sum())
                result += ddata.dot(v_data[di]*value/vnorm)
        if normalize:
            result = normalize_csr(result)
        return result

