"""Indexer of crossmap data for NN search
"""

import logging
import nmslib
from os.path import exists
from logging import info, warning
from scipy.sparse import csr_matrix, vstack
from .features import feature_map
from .db import CrossmapDB
from .tokens import CrossmapTokenizer
from .encoder import CrossmapEncoder
from .distance import all_zero, euc_dist


# this removes the INFO messages from nmslib
logging.getLogger('nmslib').setLevel(logging.WARNING)


def sparse_to_list(v):
    """convert a one-row sparse matrix into a list"""
    return v.toarray()[0]


def _remove_null_items(data, names):
    """eliminate data vectors that are null"""

    # identify problematic items
    n = len(data)
    skip = set()
    for i in range(n):
        if all_zero(data[i].toarray()[0]):
            skip.add(i)
    if len(skip) == 0:
        return data, names
    skipped = [str(names[i]) for i in range(n) if i in skip]
    s_str = "\n".join(skipped)
    w_str = "Skipping items - null vectors - "
    warning(w_str + str(len(skipped)) + "\n" + s_str)
    data = [data[i] for i in range(n) if i not in skip]
    names = [names[i] for i in range(n) if i not in skip]
    return data, names


class CrossmapIndexer:
    """Indexing data for crossmap"""

    def __init__(self, settings, features=None):
        """

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        self.settings = settings
        tokenizer = CrossmapTokenizer(settings)
        self.db = CrossmapDB(self.settings.db_file())
        self.db.build()
        if self.db.count_features() == 0:
            if features is not None:
                self.feature_map = {k: (i, 1) for i, k in enumerate(features)}
                self.db.n_features = len(features)
            else:
                self.feature_map = feature_map(settings)
                self.db.set_feature_map(self.feature_map)
        else:
            if features is not None:
                warning("features in constructor will be ignored")
            self.feature_map = self.db.get_feature_map()
        self.encoder = CrossmapEncoder(self.feature_map, tokenizer)
        self.indexes = []
        self.index_files = []
        self.target_ids = None

    def clear(self):
        self.indexes = []
        self.index_files = []

    def _build_index_none(self, label=""):
        """a helper to build an empty index"""

        warning("Skipping build index for " + label + " - no data")
        self.indexes.append(None)
        self.index_files.append(None)

    def _build_index(self, files, label=""):
        """builds an Annoy index using data from documents on disk"""

        if len(files) == 0:
            self._build_index_none(label)
            return

        index_file = self.settings.index_file(label)
        if exists(index_file):
            warning("Skipping build index for " + label + " - already exists")
            self._load_index(label)
            return

        info("Building index for " + label)
        items, item_names = self.encoder.documents(files)
        items, item_names = _remove_null_items(items, item_names)
        info("Number of items: "+str(len(item_names)))
        self.db._add_data(items, item_names, tab=label)
        items = vstack(items)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.addDataPointBatch(items)
        result.createIndex(print_progress=False)
        self.indexes.append(result)
        self.index_files.append(index_file)
        result.saveIndex(index_file, save_data=True)

    def build(self):
        """construct indexes from targets and other documents"""

        # build an index just for the targets, then just for documents
        settings = self.settings
        self.clear()
        self._build_index(settings.files("targets"), "targets")
        self._build_index(settings.files("documents"), "documents")
        self._target_ids()

    def _load_index(self, label=""):
        index_file = self.settings.index_file(label)
        if not exists(index_file):
            warning("Skipping loading index for " + label)
            self.indexes.append(None)
            self.index_files.append(None)
            return

        info("Loading index for " + label)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.loadIndex(index_file, load_data=True)
        self.indexes.append(result)
        self.index_files.append(index_file)

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        self._load_index("targets")
        self._load_index("documents")
        self._target_ids()

    def _target_ids(self):
        """grab a map of target indexes and ids"""
        self.target_ids = self.db.all_ids(table="targets")

    def _neighbors(self, v, n=5, index=0, names=False):
        """get a set of neighbors for a document"""

        if self.indexes[index] is None:
            return [], []
        get_nns = self.indexes[index].knnQueryBatch
        temp = get_nns(csr_matrix(v), n)
        nns, distances = temp[0][0], temp[0][1]
        nns = [int(_) for _ in nns]
        if names:
            nns = self.db.ids(nns, table=index)
        return nns, distances

    def encode_document(self, doc):
        result, _ = self.encoder.document(doc)
        return result

    def nearest_targets(self, v, n=5):
        return self._neighbors(v, n, index=0, names=True)

    def nearest_documents(self, v, n=5):
        return self._neighbors(v, n, index=1, names=True)

    def suggest_targets(self, v, n=5, n_doc=5):
        """suggest nearest neighbors for a vector

        Arguments:
            v     list with float values
            n     integer, number of suggestions
            n_doc integer, number of helper documents

        Returns:
            two lists:
            first list has with target ids
            second list has composite/weighted distances
        """
        v = csr_matrix(v)
        vlist = sparse_to_list(v)
        db = self.db

        # get direct distances from vector to targets
        nn0, dist0 = self._neighbors(v, n, index=0)
        target_dist = {i: d for i, d in zip(nn0, dist0)}
        target_data = dict()
        hits_targets = db.get_targets(idxs=nn0)
        for _, val in enumerate(hits_targets):
            target_data[val["idx"]] = sparse_to_list(val["data"])
        # collect relevant documents
        nn1, dist1 = self._neighbors(v, n_doc, index=1)
        hit_docs = db.get_documents(idxs=nn1)
        doc_data = dict()
        for _, val in enumerate(hit_docs):
            doc_data[val["idx"]] = sparse_to_list(val["data"])

        # record distances from docs to targets
        # (some docs may introduce new targets to consider)
        doc_target_dist = dict()
        for i_doc in nn1:
            i_doc_data = doc_data[i_doc]
            nn2, dist2 = self._neighbors(i_doc_data, n, index=0)
            doc_target_dist[i_doc] = {j: d for j, d in zip(nn2, dist2)}
            for i_target in nn2:
                if i_target in target_dist:
                    continue
                i_target_data = db.get_targets(idxs=[i_target])[0]
                target_data[i_target] = sparse_to_list(i_target_data["data"])
                target_dist[i_target] = euc_dist(target_data[i_target], vlist)

        # compute weighted distances from vector to targets
        result = target_dist.copy()
        for i, d_v_i in zip(nn1, dist1):
            i_data = doc_data[i]
            i_target_dist = doc_target_dist[i]
            for j in target_dist.keys():
                if j in i_target_dist:
                    d_i_j = i_target_dist[j]
                else:
                    d_i_j = euc_dist(i_data, target_data[j])
                result[j] += (d_v_i + d_i_j)/n_doc

        result = sorted(result.items(), key=lambda x: x[1])
        suggestions = [self.target_ids[i] for i, _ in result]
        distances = [float(d) for _, d in result]
        return suggestions, distances

