"""
Crossmap class
"""

from yaml import dump
from logging import info, warning, error
from os import mkdir
from os.path import exists
from scipy.sparse import csr_matrix, vstack
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .diffuser import CrossmapDiffuser
from .vectors import csr_residual, vec_decomposition, sparse_to_dense
from .csr import dimcollapse_csr
from .tools import open_file, yaml_document, time


def search_result(ids, distances, name):
    """structure an object describing a nearest-neighbor search"""
    return dict(query=name, targets=ids, distances=distances)


def decomposition_result(ids, weights, name):
    """structure an object descripting a greedy-nearest-decomposition"""
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
        # (preserve existing metadata fields, perhaps add new fields)
        if "metadata" not in doc or type(doc["metadata"]) is not dict:
            doc["metadata"] = dict()
        if metadata is not None:
            for k, v in metadata:
                doc["metadata"][k] = v
        doc["metadata"]["timestamp"] = time()
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
        info("Added "+str(len(result))+ " entries")
        self.indexer.rebuild_index(dataset)
        return result

    def _diffuse(self, v, diffusion):
        if diffusion is None:
            return v
        return self.diffuser.diffuse(v, diffusion)

    def search(self, doc, dataset, n=3, paths=None, diffusion=None,
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
        if sum(v.data) == 0:
            return search_result([], [], query_name)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)
        suggest = self.indexer.suggest
        targets, distances = suggest(v, dataset, n, paths)
        result = search_result(targets[:n], distances[:n], query_name)
        return result

    def decompose(self, doc, dataset, n=3, paths=None, diffusion=None,
                  query_name="query"):
        """decompose of a query document in terms of targets

        :param doc: dict-like object with "data", "aux_pos" and "aux_neg"
        :param dataset: string, identifier for dataset
        :param n: integer, number of target to report
        :param paths: dict, map passed to search function
        :param diffusion: dict, strength of diffusion on primary data
        :param query_name:  character, a name for the document
        :return: dictionary containing an id, and list with target ids and
            decomposition coefficients
        """

        ids, coefficients, components = [], [], []
        suggest = self.indexer.suggest
        get_data = self.indexer.db.get_data
        decompose = vec_decomposition
        # representation of the query document
        q = self.indexer.encode_document(doc)
        q_indexes = set(q.indices)
        q = self._diffuse(q, diffusion)
        q_dense = q.toarray()
        # loop for greedy decomposition
        q_residual = q
        while len(components) < n and len(q_residual.data) > 0:
            target, _ = suggest(q_residual, dataset, 1, paths)
            target_data = get_data(dataset, ids=target)
            if target[0] in ids:
                # residual mapped back onto an existing hit? quit early
                break
            ids.append(target[0])
            target_vec = target_data[0]["data"]
            components.append(dimcollapse_csr(target_vec, q_indexes))
            basis = vstack(components)
            q_modeled = q_dense
            if set(basis.indices) is not q_indexes:
                q_modeled = dimcollapse_csr(q, set(basis.indices)).toarray()
            coefficients = decompose(q_modeled, basis.toarray())
            if coefficients[-1] == 0:
                break
            weights = csr_matrix(coefficients)
            q_residual = csr_residual(q, basis, weights)

        # order the coefficients (decreasing size, most important first)
        if len(coefficients) > 0:
            # re-do decomposition using the entire q vector
            coefficients = decompose(q_dense, basis.toarray())
            coefficients, ids = _ranked_decomposition(coefficients, ids)

        return decomposition_result(ids, coefficients, query_name)

    def search_file(self, filepath, dataset, n, paths=None, diffusion=None):
        """find nearest targets for all documents in a file

        :param filepath: string, path to a file with documents
        :param dataset: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param paths: dict, map with number of paths through datasets
        :param diffusion: dict, map with diffusion strengths
        :return: list with dicts, each as output by search()
        """

        return _action_file(self.search, filepath, dataset=dataset,
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

        return _action_file(self.decompose, filepath, dataset=dataset,
                            n=n, paths=paths, diffusion=diffusion)

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


def _action_file(action, filepath, **kw):
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


def _ranked_decomposition(coefficients, ids):
    """order paired values+strings, removing zeros

    :param coefficients: csr_matrix, one-column vertical vector
    :param ids: list of string identifiers
    :return: a list of coefficients, a list of matched identifiers.
        Output is ranked, very small items are removed
    """

    temp = [_ for _ in coefficients[:, 0]]
    coefficients, ids = zip(*sorted(zip(temp, ids), reverse=True))
    zeros = [i for i, v in enumerate(coefficients) if v==0]
    if len(zeros) == 0:
        return coefficients, ids
    ids = [_ for i, _ in enumerate(ids) if i not in zeros]
    coefficients = [_ for i,_ in enumerate(coefficients) if i not in zeros]
    return coefficients, ids
