"""Crossmap class"""

import functools
from os import mkdir
from os.path import exists
from scipy.sparse import csr_matrix, vstack
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .vectors import csr_residual, vec_decomposition
from .tools import open_file, yaml_document


def require_valid(f):
    """Decorator, check if class is valid before computation."""

    @functools.wraps(f)
    def wrapped(self, *args, **kw):
        if self.valid():
            return f(self, *args, **kw)
        return None

    return wrapped


def prediction(ids, distances, name):
    """structure an object describing a nn prediction"""
    return dict(query=name, targets=ids, distances=distances)


def decomposition(ids, weights, name):
    """structure an object descripting a gnd decomposition"""
    return dict(query=name, targets=ids, coefficients=weights)


class Crossmap:

    def __init__(self, settings):
        """configure a crossmap object.

        :param settings: a CrossmapSettings object, or a path to a configuration file
        """

        if type(settings) is str:
            settings = CrossmapSettings(settings)
        self.settings = settings
        if not settings.valid:
            return

        # ensure directories exist
        if not exists(self.settings.data_dir):
            mkdir(self.settings.data_dir)

        # prepare objects
        self.indexer = CrossmapIndexer(settings)
        self.encoder = self.indexer.encoder

    @property
    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid and self.indexer.valid

    def build(self):
        """create indexes and auxiliary objects"""
        self.indexer.build()
        self.indexer.db.index()

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()

    def predict(self, doc, n_targets=3, n_docs=3, query_name="query"):
        """identify targets that are close to the input query

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param n_targets: integer, number of target to report
        :param n_docs: integer, number of documents to use in the calculation
        :param query_name: character, a name for the document
        :return: a dictionary containing an id, and lists to target ids and
            distances
        """

        n = n_targets
        doc_data = self.indexer.encode_document(doc)
        if doc_data.sum() == 0:
            return prediction([], [], query_name)
        suggest_targets = self.indexer.suggest_targets
        targets, distances = suggest_targets(doc_data, n, n_docs)
        return prediction(targets[:n], distances[:n], query_name)

    def decompose(self, doc, n_targets=3, n_docs=3, query_name="query"):
        """provide a decomposition of a query in terms of targets

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param n_targets: integer, number of target to report
        :param n_docs: integer, number of documents to use in the calculation
        :param query_name:  character, a name for the document
        :return: dictionary containing an id, and list with target ids and
            decomposition coefficients
        """

        ids, components, distances = [], [], []
        # shortcuts to functions
        suggest_targets = self.indexer.suggest_targets
        get_targets = self.indexer.db.get_targets
        decompose = vec_decomposition
        # representation of the query document
        q = self.indexer.encode_document(doc)
        q_residual, q_dense = q.copy(), q.toarray()
        coefficients = []
        # loop for greedy decomposition
        while len(components) < n_targets and q_residual.sum() > 0:
            target, _ = suggest_targets(q_residual, 1, n_docs)
            target_data = get_targets(ids=target)
            if target[0] not in ids:
                ids.append(target[0])
                components.append(target_data[0]["data"])
                basis = vstack(components)
                coefficients = decompose(q_dense, basis.toarray())
            else:
                # residual mapped back onto self?
                # change the last coefficient (it's a hack)
                coefficients[len(coefficients)-1] *= 2
            q_residual = csr_residual(q, basis, csr_matrix(coefficients))

        # this handles case when the loop doesn't run as well as when
        # as when the loop produces a column vector
        if len(coefficients) > 0:
            coefficients = [_ for _ in coefficients[:, 0]]

        return decomposition(ids, coefficients, query_name)

    def predict_file(self, filepath, n_targets=3, n_docs=3):
        """perform predictions of nearest targets for documents defined in a file

        :param filepath: character, path to a file with documents
        :param n_targets: integer, number of target to report for each input
        :param n_docs: integer, number of documents to use in the calculation
        :return: vector with dicts, each as output by predict()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.predict(doc, n_targets, n_docs, id))
        return result

    def decompose_file(self, filepath, n_targets=3, n_docs=3):
        """perform decomposition for documents defined in a file

        :param filepath: character, path to a file with documents
        :param n_targets: integer, number of target to report for each input
        :param n_docs: integer, number of documents to use in the calculation
        :return: vector with dicts, each as output by decompose()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.decompose(doc, n_targets, n_docs, id))
        return result

