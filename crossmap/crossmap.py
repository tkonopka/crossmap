"""Crossmap class"""

from os import mkdir
from os.path import exists
from scipy.sparse import csr_matrix, vstack
from .distance import sparse_euc_distance
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .vectors import csr_residual, vec_decomposition, sparse_to_dense
from .tools import open_file, yaml_document


def prediction_result(ids, distances, name):
    """structure an object describing a nn prediction"""
    return dict(query=name, targets=ids, distances=distances)


def decomposition_result(ids, weights, name):
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
        self.indexer = None
        if not settings.valid:
            return

        # ensure directories exist
        if not exists(self.settings.prefix):
            mkdir(self.settings.prefix)

        # prepare objects
        self.indexer = CrossmapIndexer(settings)
        self.encoder = self.indexer.encoder

    @property
    def valid(self):
        """get a boolean stating whether settings are valid"""
        if self.indexer is None:
            return False
        if not self.settings.valid:
            return False
        return self.indexer.valid

    def build(self):
        """create indexes and auxiliary objects"""

        if self.settings.valid:
            self.indexer.build()
            self.indexer.db.index()

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()

    def predict(self, doc, label, n=3, aux=None, diffuse=None,
                query_name="query", ):
        """identify targets that are close to the input query

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param label: string, identifier for dataset to look for targets
        :param n: integer, number of target to report
        :param aux: dict, map linking auxiliary dataset labels and number of
        documents to use from those datasets
        :param diffuse: dict, map assigning diffusion weights
        :param query_name: character, a name for the document
        :return: a dictionary containing an id, and lists to target ids and
            distances
        """

        v = self.indexer.encode_document(doc)
        if v.sum() == 0:
            return prediction_result([], [], query_name)
        suggest = self.indexer.suggest
        targets, distances = suggest(v, label, n, aux)
        result = prediction_result(targets[:n], distances[:n], query_name)
        return result

    def decompose(self, doc, label, n=3, aux=None, query_name="query"):
        """decompose of a query document in terms of targets

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param label: string, identifier for dataset
        :param n: integer, number of target to report
        :param aux: dict, map passed to predict
        :param query_name:  character, a name for the document
        :return: dictionary containing an id, and list with target ids and
            decomposition coefficients
        """

        ids, components, distances = [], [], []
        # shortcuts to functions
        suggest = self.indexer.suggest
        get_data = self.indexer.db.get_data
        decompose = vec_decomposition
        # representation of the query document
        q = self.indexer.encode_document(doc)
        q_residual, q_dense = q.copy(), q.toarray()
        coefficients = []
        # loop for greedy decomposition
        while len(components) < n and q_residual.sum() > 0:
            target, _ = suggest(q_residual, label, 1, aux)
            target_data = get_data(label, ids=target)
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

        return decomposition_result(ids, coefficients, query_name)

    def predict_file(self, filepath, label,  n, aux=None):
        """predict nearest targets for all documents in a file

        :param filepath: string, path to a file with documents
        :param label: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param aux: dict, map providing number of auxiliary documents
        :return: vector with dicts, each as output by predict()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.predict(doc, label, n, aux, query_name=id))
        return result

    def decompose_file(self, filepath, label, n=3, aux=None):
        """perform decomposition for documents defined in a file

        :param filepath: string, path to a file with documents
        :param label: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param n_docs: integer, number of documents to use in the calculation
        :return: vector with dicts, each as output by decompose()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.decompose(doc, label, n, aux,
                                             query_name=id))
        return result

    def distance(self, doc, ids=[], query_name="query"):
        """compute distances from one document to specific items in db

        :param doc: dictionary with text
        :param ids: array of string ids, targets or documents
        :return: list of objects containing id and distance
        """

        result = []
        doc_data = self.indexer.encode_document(doc)
        distance = sparse_euc_distance
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    x_vector = x_data[0]["data"]
                    x_dist = distance(doc_data, x_vector)
                    x_result = dict(query=query_name, dataset=label,
                                    id=x, distance=x_dist)
                    result.append(x_result)

        return result

    def distance_file(self, filepath, ids=[]):
        """compute distances from items in a file to specific items in db

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :return: list
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.distance(doc, ids, query_name=id))
        return result

    def vectors(self, filepath, ids=[]):
        """

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :return: list
        """

        result = []

        # convert db items into vectors
        db = self.indexer.db
        for x in ids:
            x_target = db.get_targets(ids=[x])
            x_doc = db.get_documents(ids=[x])
            x_result = dict()
            if len(x_target) > 0:
                x_vector = x_target[0]["data"]
                x_result["target"] = x
            elif len(x_doc) > 0:
                x_vector = x_doc[0]["data"]
                x_result["document"] = x
            else:
                continue
            x_result["vector"] = list(sparse_to_dense(x_vector))
            result.append(x_result)

        if filepath is None:
            return result

        # convert from-file items into vectors
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                doc_vec = self.indexer.encode_document(doc)
                doc_vec = list(sparse_to_dense(doc_vec))
                result.append(dict(id=id, vector=doc_vec))
        return result

