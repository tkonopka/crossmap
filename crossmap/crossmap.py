"""
Crossmap class
"""

from logging import warning, error
from os import mkdir
from os.path import exists
from scipy.sparse import csr_matrix, vstack
from .distance import sparse_euc_distance
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .diffuser import CrossmapDiffuser
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
        """declare a minimal crossmap object.

        :param settings: a CrossmapSettings object, or a path to a
            configuration file
        """

        if type(settings) is str:
            settings = CrossmapSettings(settings)
        self.settings = settings
        self.indexer = None
        if not settings.valid:
            return

        if not exists(self.settings.prefix):
            mkdir(self.settings.prefix)

        self.indexer = CrossmapIndexer(settings)
        self.encoder = self.indexer.encoder
        self.diffuser = None
        self.default_label = list(self.settings.data_files.keys())[0]

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

        if not self.settings.valid:
            return
        self.indexer.build()
        self.indexer.db.index("data")
        self.diffuser = CrossmapDiffuser(self.settings)
        self.diffuser.build()
        self.diffuser.db.index("counts")

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()
        self.diffuser = CrossmapDiffuser(self.settings)

    def add(self, doc, label, id, metadata=None):
        """add a new item into the db

        :param doc: dict with string data
        :param label: string, name of dataset to append
        :param id: string, identifier for new item
        :param metadata: dict, a free element of additional information
        :return:
        """

        raise Exception("not implemented yet")

    def predict(self, doc, label, n=3, aux=None, diffusion=None,
                query_name="query"):
        """identify targets that are close to the input query

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param label: string, identifier for dataset to look for targets
        :param n: integer, number of target to report
        :param aux: dict, map linking auxiliary dataset labels and number of
            documents to use from those datasets
        :param diffusion: dict, map assigning diffusion weights
        :param query_name: character, a name for the document
        :return: a dictionary containing an id, and lists to target ids and
            distances
        """

        v = self.indexer.encode_document(doc)
        if v.sum() == 0:
            return prediction_result([], [], query_name)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)
        suggest = self.indexer.suggest
        targets, distances = suggest(v, label, n, aux)
        result = prediction_result(targets[:n], distances[:n], query_name)
        return result

    def decompose(self, doc, label, n=3, aux=None, diffusion=None,
                  query_name="query"):
        """decompose of a query document in terms of targets

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param label: string, identifier for dataset
        :param n: integer, number of target to report
        :param aux: dict, map passed to predict
        :param diffusion: dict, strength of diffusion on primary data
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
        if diffusion is not None:
            q = self.diffuser.diffuse(q, diffusion)
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

    def predict_file(self, filepath, label, n, aux=None, diffusion=None):
        """predict nearest targets for all documents in a file

        :param filepath: string, path to a file with documents
        :param label: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param aux: dict, map providing number of auxiliary documents
        :param diffusion: dict, map with diffusion strengths
        :return: vector with dicts, each as output by predict()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.predict(doc, label, n, aux, diffusion,
                                           query_name=id))
        return result

    def decompose_file(self, filepath, label, n=3, aux=None, diffusion=None):
        """perform decomposition for documents defined in a file

        :param filepath: string, path to a file with documents
        :param label: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param aux: dict, number of auxiliary documents
        :param diffusion: dict, map with diffusion strengths
        :return: vector with dicts, each as output by decompose()
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.decompose(doc, label, n, aux, diffusion,
                                             query_name=id))
        return result

    def distance(self, doc, ids=[], diffusion=None, query_name="query"):
        """compute distances from one document to specific items in db

        :param doc: dictionary with text
        :param ids: array of string ids, targets or documents
        :param diffusion: dict, map of diffusion strengths
        :param query_name: string, an identifier to associate with the doc
        :return: list of objects containing id and distance
        """

        result = []
        v = self.indexer.encode_document(doc)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)
        distance = sparse_euc_distance
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    x_vector = x_data[0]["data"]
                    x_dist = distance(v, x_vector)
                    x_result = dict(query=query_name, dataset=label,
                                    id=x, distance=x_dist)
                    result.append(x_result)

        return result

    def distance_file(self, filepath, ids=[], diffuse=None):
        """compute distances from items in a file to specific items in db

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffuse: dict, map of diffusion strengths
        :return: list
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.distance(doc, ids, diffuse, query_name=id))
        return result

    def vectors(self, filepath, ids=[], diffuse=None):
        """extraction of feature vectors

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffuse: dict, map of diffusion strengths
        :return: list
        """

        result = []

        # convert db items into vectors
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    v = x_data[0]["data"]
                    if diffuse is not None:
                        v = self.diffuser.diffuse(v, diffuse)
                    v = list(sparse_to_dense(v))
                    x_result = dict(dataset=label, id=x, vector=v)
                    result.append(x_result)

        if filepath is None:
            return result

        # convert from-file items into vectors
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                v = self.indexer.encode_document(doc)
                if diffuse is not None:
                    v = self.diffuser.diffuse(v, diffuse)
                v = list(sparse_to_dense(v))
                result.append(dict(dataset="_file_", id=id, vector=v))
        return result

    def counts(self, label, features=[], digits=6):
        """extract count vectors associated with features

        :param features: list of features
        :return:
        """

        # convert features into indexes, and an inverse mapping
        fm, ifm = self.indexer.feature_map, dict()
        idxs = []
        for f in features:
            if f in fm:
                ifm[fm[f][0]] = f
                idxs.append(fm[f][0])

        counts = self.indexer.db.get_counts(label, idxs)
        result = []
        for k, v in counts.items():
            vlist = list(sparse_to_dense(v))
            vmax = max(vlist)
            vlist = [round(_/vmax, digits) for _ in vlist]
            result.append(dict(feature=ifm[k], counts=vlist))
        return result

    def features(self):
        """extract feature information"""

        result = []
        for k, v in self.indexer.feature_map.items():
            result.append(dict(feature=k, index=v[0], weight=v[1]))
        return result

    def summary(self, digits=4):
        """prepare an ad-hoc summary of the contents of the configuration"""

        def stats(x):
            if len(x) == 0:
                return {"min": 0, "mean": 0, "max": 0}
            temp = dict(min=min(x), mean=sum(x)/len(x), max=max(x))
            return {k: round(v, digits) for k, v in temp.items()}

        db = self.indexer.db
        datasets = []
        for label in db.datasets:
            size = db.dataset_size(label)
            counts_sparsity = stats(db.sparsity(label, "counts"))
            data_sparsity = stats(db.sparsity(label, "data"))
            datasets.append(dict(label=label, size=size,
                                 counts_sparsity=counts_sparsity,
                                 data_sparsity=data_sparsity))

        return dict(name=self.settings.name,
                    dir=self.settings.dir,
                    features=len(self.indexer.feature_map),
                    datasets=datasets)


def validate_dataset_label(crossmap, label=None, log=True):
    """check for a valid dataset label

    :param crossmap: object of class Crossmap
    :param label: string, a dataset identifier, set None to get default
    :param log: boolean, toggle log messages
    :return: a validated dataset string, a default label if None is specified,
        or None if specified label is invalid
    """

    if label is None:
        label = str(crossmap.default_label)
        if log:
            warning("using default dataset: " + label)
    if label not in crossmap.indexer.db.datasets:
        if log:
            error("dataset label is not valid: " + label)
        label = None
    return label
