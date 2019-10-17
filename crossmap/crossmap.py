"""
Crossmap class
"""

from yaml import dump
from logging import warning, error
from os import mkdir
from os.path import exists
from scipy.sparse import csr_matrix, vstack
from .distance import sparse_euc_distance
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .diffuser import CrossmapDiffuser
from .vectors import csr_residual, vec_decomposition, sparse_to_dense
from .tools import open_file, yaml_document, time


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
        self.db = None
        if not settings.valid:
            return

        if not exists(self.settings.prefix):
            mkdir(self.settings.prefix)

        self.indexer = CrossmapIndexer(settings)
        self.db = self.indexer.db
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
        self.diffuser = CrossmapDiffuser(self.settings, db=self.indexer.db)
        self.diffuser.build()
        self.diffuser.db.index("counts")

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()
        self.diffuser = CrossmapDiffuser(self.settings, self.indexer.db)

    def add(self, dataset, doc, id, metadata=None, rebuild=True):
        """add a new item into the db

        :param dataset: string, name of dataset to append
        :param doc: dict with string data
        :param id: string, identifier for new item
        :param metadata: dict, a free element of additional information
        :param rebuild: logical, set True to rebuild nearest-neighbor indexing
        :return: an integer signaling
        """

        if dataset in self.settings.data_files:
            raise Exception("cannot add to file-based datasets")
        label_status = self.db.validate_dataset_label(dataset)
        if label_status < 0:
            raise Exception("invalid dataset label: " + str(dataset))
        if label_status:
            self.db.register_dataset(dataset)

        # update the db structures (indexing and diffusion)
        idx = self.indexer.update(dataset, doc, id, rebuild=rebuild)
        self.diffuser.update(dataset, [idx])

        # record the item in a disk file
        if metadata is None:
            metadata = dict()
        metadata["timestamp"] = time()
        doc["metadata"] = metadata
        with open(self.settings.yaml_file(dataset), "at") as f:
            f.write(dump({id: doc}))

        return idx

    def add_file(self, dataset, filepath):
        """transfer items from a data file into a new dataset in the db

        :param dataset:
        :param filepath:
        :return: list with the added ids
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.add(dataset, doc, id, rebuild=False))
        self.indexer.rebuild_index(dataset)
        return result

    def predict(self, doc, dataset, n=3, paths=None, diffusion=None,
                query_name="query"):
        """identify targets that are close to the input query

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param dataset: string, identifier for dataset to look for targets
        :param n: integer, number of target to report
        :param paths: dict, map linking dataset labels to number of
            paths from query to targets through those datasets
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
        targets, distances = suggest(v, dataset, n, paths)
        result = prediction_result(targets[:n], distances[:n], query_name)
        return result

    def decompose(self, doc, dataset, n=3, paths=None, diffusion=None,
                  query_name="query"):
        """decompose of a query document in terms of targets

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param dataset: string, identifier for dataset
        :param n: integer, number of target to report
        :param paths: dict, map passed to predict
        :param diffusion: dict, strength of diffusion on primary data
        :param query_name:  character, a name for the document
        :return: dictionary containing an id, and list with target ids and
            decomposition coefficients
        """

        ids, components, distances = [], [], []
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
            target, _ = suggest(q_residual, dataset, 1, paths)
            target_data = get_data(dataset, ids=target)
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

    def _action_file(self, action, filepath, **kw):
        """applies an action function to contents of a file

        :param action: function
        :param filepath: string, path to a file with yaml documents
        :param kw: keyword arguments, all passed on to action
        :return: list with result of action function on the documents in the file
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(action(doc, **kw, query_name=id))
        return result

    def predict_file(self, filepath, dataset, n, paths=None, diffusion=None):
        """predict nearest targets for all documents in a file

        :param filepath: string, path to a file with documents
        :param dataset: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param paths: dict, map with number of paths through datasets
        :param diffusion: dict, map with diffusion strengths
        :return: list with dicts, each as output by predict()
        """

        return self._action_file(self.predict, filepath, dataset=dataset,
                                 n=n, paths=paths, diffusion=diffusion)

    def decompose_file(self, filepath, dataset, n=3, paths=None, diffusion=None):
        """perform decomposition for documents defined in a file

        :param filepath: string, path to a file with documents
        :param dataset: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param paths: dict, map with number of paths through datasets
        :param diffusion: dict, map with diffusion strengths
        :return: list with dicts, each as output by decompose()
        """

        return self._action_file(self.decompose, filepath, dataset=dataset,
                                 n=n, paths=paths, diffusion=diffusion)

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

        db = self.db
        datasets = []
        for dataset in db.datasets:
            size = db.dataset_size(dataset)
            counts_sparsity = stats(db.sparsity(dataset, "counts"))
            data_sparsity = stats(db.sparsity(dataset, "data"))
            datasets.append(dict(label=dataset, size=size,
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
    if label not in crossmap.db.datasets:
        if log:
            error("dataset label is not valid: " + label)
        label = None
    return label

