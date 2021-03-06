"""
Crossmap class
"""

from contextlib import suppress
from yaml import dump
from logging import info, warning, error
from os import mkdir, remove
from os.path import exists
from shutil import rmtree
from scipy.sparse import vstack
from .settings import CrossmapSettings
from .dbmongo import CrossmapMongoDB as CrossmapDB
from .indexer import CrossmapIndexer
from .diffuser import CrossmapDiffuser
from .vectors import csr_residual
from .vectors import vec_decomposition as vec_decomp
from .csr import FastCsrMatrix, dimcollapse_csr
from .tools import open_file, yaml_document, time


def _search_result(ids, distances, name):
    """structure an object describing a nearest-neighbor search

    :param ids: list of string identifiers
    :param distances: list of numeric values
    :param name: query name included in the output dictionary
    :return: dictionary, contain lists with ids and distances,
      ordered by distance from smallest to largerst
    """

    return dict(query=name, targets=ids, distances=distances)


def _decomposition_result(ids, weights, name):
    """structure an object describing a greedy-nearest-decomposition"""
    return dict(query=name, targets=ids, coefficients=weights)


def _ranked_decomposition(coefficients, ids):
    """order paired values+strings, removing zeros

    :param coefficients: csr_matrix, one-column vertical vector
    :param ids: list of string identifiers
    :return: a list of coefficients, a list of matched identifiers.
        Output is ranked, very small items are removed
    """

    temp = [_ for _ in coefficients[:, 0]]
    coefficients, ids = zip(*sorted(zip(temp, ids), reverse=True))
    zeros = [i for i, v in enumerate(coefficients) if v == 0]
    if len(zeros) == 0:
        return coefficients, ids
    ids = [_ for i, _ in enumerate(ids) if i not in zeros]
    coefficients = [_ for i, _ in enumerate(coefficients) if i not in zeros]
    return coefficients, ids


def remove_db_and_files(settings):
    """clean up database and data files (leaves settings object)"""

    if type(settings) is str:
        settings = CrossmapSettings(settings)
    db = CrossmapDB(settings)
    info("Removing database: " + db.db_name)
    db.remove()
    info("Removing directory: " + settings.prefix)
    if exists(settings.prefix):
        with suppress(OSError):
            rmtree(settings.prefix)


class Crossmap:

    def __init__(self, settings):
        """a standard crossmap object.

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
        if not exists(settings.prefix):
            mkdir(settings.prefix)
        self.db = CrossmapDB(settings)
        self.indexer = CrossmapIndexer(settings, db=self.db)
        self.db = self.indexer.db
        self.encoder = self.indexer.encoder
        self.diffuser = None
        # determine a default dataset for querying
        self.default_label = settings.data.default
        if self.default_label is None:
            if len(self.db.datasets):
                self.default_label = list(self.db.datasets.keys())[0]
            else:
                raise Exception("could not determine default dataset")

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
        self.db.index("data")
        self.diffuser = CrossmapDiffuser(self.settings, db=self.db)
        self.diffuser.build()
        self.db.index("counts")
        info("done")

    def load(self):
        """load indexes from prepared files"""

        self.indexer.load()
        self.diffuser = CrossmapDiffuser(self.settings, self.db)

    def remove(self, dataset):
        """remove a dataset, or entire instance"""

        self.db.remove_dataset(dataset)
        dataset_files = [self.settings.yaml_file(dataset),
                         self.settings.index_file(dataset),
                         self.settings.index_dat_file(dataset)]
        for f in dataset_files:
            if exists(f):
                remove(f)
        # reload the instance (updates indexer, diffuser)
        self.load()

    def add(self, dataset, doc, id, metadata=None, rebuild=True):
        """add a new item into the db

        :param dataset: string, name of dataset to append
        :param doc: dict with string data
        :param id: string, identifier for new item
        :param metadata: dict, a free element of additional information
        :param rebuild: logical, set True to rebuild nearest-neighbor indexing
        :return: an integer signaling
        """

        if dataset in self.settings.data.collections:
            raise Exception("cannot add to file-based datasets")
        label_status = self.db.validate_dataset_label(dataset)
        if label_status < 0:
            raise Exception("invalid dataset label: " + str(dataset))
        if label_status:
            info("Registering dataset: " + str(dataset))
            self.db.register_dataset(dataset)

        # update the db structures (indexing and diffusion)
        idx = self.indexer.update(dataset, doc, id, rebuild=rebuild)
        self.diffuser.update(dataset, [idx])

        # record the item in a disk file
        # (preserve existing metadata fields, perhaps add new fields)
        if "metadata" not in doc or type(doc["metadata"]) is not dict:
            doc["metadata"] = dict()
        if metadata is not None:
            for k, v in metadata.items():
                doc["metadata"][k] = v
        if "timestamp" not in doc["metadata"]:
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
        info("Added "+str(len(result)) + " entries")
        self.indexer.rebuild_index(dataset)
        return result

    def _prep_vector(self, doc, diffusion=None):
        """prepare text document into sparse vectors

        :param doc: dictionary with component data, data_pos, etc.
        :param diffusion: dictionary with diffusion strengths
        :return: two csr vectors, a raw encoding and a diffused encoding
        """

        v = self.encoder.document(doc)
        if diffusion is None:
            return v, v
        return v, self.diffuser.diffuse(v, diffusion)

    def diffuse(self, doc, diffusion=None, query_name="", **kwargs):
        """provide an explanation for diffusion of a document into features

        :param doc: dict-like object with "data", "data_pos" and "data_neg"
        :param diffusion: dict, map assigning diffusion weights
        :param query_name: character, a name for the document
        :param kwargs: other keyword arguments, ignored
            (This is included for consistency with search() and decompose())
        :return: a dictionary containing an id, and feature weights
        """

        inv_feature_map = self.encoder.inv_feature_map
        raw, diffused = self._prep_vector(doc, diffusion)
        data = []
        for i, d in zip(diffused.indices, diffused.data):
            data.append([abs(d), round(d, 6), inv_feature_map[i]])
        data = sorted(data, reverse=True)
        data = [{"feature": v[2], "value": v[1]} for i, v in enumerate(data)]
        return dict(query=query_name, features=data)

    def search(self, doc, dataset, n=3, diffusion=None, query_name="query",
               **kwargs):
        """identify targets that are close to the input query

        :param doc: dict-like object with "data", "data_pos" and "data_neg"
        :param dataset: string, identifier for dataset to look for targets
        :param n: integer, number of target to report
        :param diffusion: dict, map assigning diffusion weights
        :param query_name: character, a name for the document
        :param kwargs: other keyword arguments, ignored
            (This is included for consistency with search() and decompose())
        :return: a dictionary containing an id, and lists to target ids and
            distances
        """

        raw, diffused = self._prep_vector(doc, diffusion)
        if len(raw.data) == 0:
            return _search_result([], [], query_name)
        suggest = self.indexer.suggest
        targets, distances = suggest(diffused, dataset, n)
        return _search_result(targets, distances, query_name)

    def decompose(self, doc, dataset, n=3, diffusion=None,
                  factors=None,
                  query_name="query"):
        """decompose of a query document in terms of targets

        :param doc: dict-like object with "data", "data_pos" and "data_neg"
        :param dataset: string, identifier for dataset
        :param n: integer, number of target to report
        :param diffusion: dict, strength of diffusion on primary data
        :param factors: list with item ids that must be included in the
            decomposition
        :param query_name:  character, a name for the document
        :return: dictionary containing an id, and list with target ids and
            decomposition coefficients
        """

        # shortcuts
        suggest = self.indexer.suggest
        get_data = self.indexer.db.get_data
        # representation of the query document, raw and diffused
        q_raw, q = self._prep_vector(doc, diffusion)
        q_indexes = set(q_raw.indices)
        q_dense = q.toarray()
        # loop for greedy decomposition
        factors = factors if factors is not None else []
        num_factors = len(factors)
        ids, coefficients, components = [], [], []
        q_residual = q
        while len(components) < n and len(q_residual.data) > 0:
            # use a suggested factors, or find a new factor via search
            if len(components) < num_factors:
                target = [factors[len(components)]]
            else:
                target, _ = suggest(q_residual, dataset, 1)
            # residual mapped back onto an existing hit? quit early
            if len(target) == 0 or target[0] in ids:
                break
            target_data = get_data(dataset, ids=target)
            ids.append(target[0])
            target_vec = target_data[0]["data"]
            components.append(dimcollapse_csr(target_vec, q_indexes))
            basis = vstack(components)
            q_modeled = q_dense
            if set(basis.indices) is not q_indexes:
                q_modeled = dimcollapse_csr(q, set(basis.indices)).toarray()
            coefficients = vec_decomp(q_modeled, basis.toarray())
            if coefficients[-1] == 0:
                break
            weights = FastCsrMatrix(coefficients)
            q_residual = csr_residual(q, basis, weights)

        # order the coefficients (decreasing size, most important first)
        if len(coefficients) > 0:
            # re-do decomposition using the entire q vector
            coefficients = vec_decomp(q_dense, basis.toarray())
            first_id = ids[0]
            coefficients, ids = _ranked_decomposition(coefficients, ids)
            if len(ids) == 0:
                coefficients, ids = [0.0], [first_id]

        return _decomposition_result(ids, coefficients, query_name)

    def search_file(self, filepath, dataset, n, diffusion=None,
                    **kwargs):
        """find nearest targets for all documents in a file

        :param filepath: string, path to a file with documents
        :param dataset: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param diffusion: dict, map with diffusion strengths
        :param kwargs: other keyword arguments, ignored
            (This is included for consistency with decompose_file())
        :return: list with dicts, each as output by search()
        """

        return _action_file(self.search, filepath, dataset=dataset,
                            n=n, diffusion=diffusion)

    def decompose_file(self, filepath, dataset, n=3, diffusion=None,
                       factors=None):
        """perform decomposition for documents defined in a file

        :param filepath: string, path to a file with documents
        :param dataset: string, identifier for target dataset
        :param n: integer, number of target to report for each input
        :param diffusion: dict, map with diffusion strengths
        :param factors: list with item ids that must be included in the
            decomposition
        :return: list with dicts, each as output by decompose()
        """

        return _action_file(self.decompose, filepath, dataset=dataset,
                            n=n, diffusion=diffusion, factors=factors)


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
    if filepath is None:
        return result
    with open_file(filepath, "rt") as f:
        for id, doc in yaml_document(f):
            if type(doc) is not dict:
                error("invalid document type: "+str(id))
                break
            result.append(action(doc, **kw, query_name=id))
    return result

