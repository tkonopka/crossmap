"""Indexer of crossmap data for NN search
"""

import nmslib
from os.path import exists
from logging import info, warning
from annoy import AnnoyIndex
from scipy.sparse import csr_matrix
from .features import feature_map
from .tokens import CrossmapTokenizer
from .tools import read_obj, write_obj
from .encoder import CrossmapEncoder
from .distance import all_zero, normalize_vec, euc_dist


def sparse_to_list(v):
    """convert a one-row sparse matrix into a list"""
    return v.toarray()[0]


class CrossmapIndexer:
    """Indexing data for crossmap"""

    def __init__(self, settings, features=None):
        """

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        self.settings = settings
        tokenizer = CrossmapTokenizer(settings)
        if features is not None:
            self.feature_map = {k: i for i, k in enumerate(features)}
        else:
            self.feature_map = feature_map(settings)
        self.encoder = CrossmapEncoder(self.feature_map, tokenizer)
        self.items = dict()
        self.item_names = []
        self.indexes = []
        self.data = []
        self.index_files = []

    def clear(self):
        self.items = dict()
        self.item_names = []
        self.indexes = []
        self.index_files = []

    def _remove_null_items(self, data, names):
        """ensure that data vectors are non-null"""

        # identify problematic items
        n = len(data)
        skip = set([i for i in range(n) if all_zero(data[i])])
        if len(skip) == 0:
            return data, names
        skipped = [str(names[i]) for i in range(n) if i in skip]
        s_str = "\n".join(skipped)
        w_str = "Skipping items - null vectors - "
        warning(w_str + str(len(skipped)) + "\n" + s_str)
        data = [data[i] for i in range(n) if i not in skip]
        names = [names[i] for i in range(n) if i not in skip]
        return data, names

    def _build_index_none(self, label=""):
        """a helper to build an empty index"""

        warning("Skipping build index for " + label + " - no data")
        self.indexes.append(None)
        self.index_files.append(None)
        self.item_names.append(None)
        self.data.append(None)

    def _build_index(self, files, label=""):
        """builds an Annoy index using data from documents on disk"""

        if len(files) == 0:
            self._build_index_none(label)
            return

        index_file = self.settings.index_file(label)
        items_file = self.settings.pickle_file(label+"-item-names")
        data_file = self.settings.pickle_file(label+"-data")
        if exists(index_file) and exists(items_file):
            warning("Skipping build index for " + label + " - already exists")
            self._load_index(label)
            return

        info("Building index for " + label)
        index_index = len(self.indexes)
        items, item_names = self.encoder.documents(files)
        info("Number of items: "+str(len(item_names)))
        items, item_names = self._remove_null_items(items, item_names)
        info("Number of items: "+str(len(item_names)))
        items = csr_matrix(items)
        self.data.append(items)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.addDataPointBatch(items)
        for i in range(len(item_names)):
            self.items[item_names[i]] = (index_index, i)
        result.createIndex(print_progress=False)
        # record the index and items names
        self.item_names.append(item_names)
        self.indexes.append(result)
        self.index_files.append(index_file)
        # cache the index and item names
        result.saveIndex(index_file, save_data=True)
        write_obj(item_names, items_file)
        write_obj(items, data_file)

    def build(self):
        """construct indexes from targets and other documents"""

        # build an index just for the targets, then just for documents
        settings = self.settings
        self.clear()
        self._build_index(settings.files("targets"), "targets")
        self._build_index(settings.files("documents"), "documents")

    def _load_index(self, label=""):
        index_file = self.settings.index_file(label)
        items_file = self.settings.pickle_file(label + "-item-names")
        data_file = self.settings.pickle_file(label + "-data")
        index_index = len(self.indexes)
        if not exists(index_file):
            warning("Skipping loading index for " + label)
            self.indexes.append(None)
            self.index_files.append(None)
            self.item_names.append(None)
            self.data.append(None)
            return

        info("Loading index for " + label)
        self.data.append(read_obj(data_file))
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.loadIndex(index_file, load_data=True)
        self.indexes.append(result)
        item_names = read_obj(items_file)
        self.item_names.append(item_names)
        self.index_files.append(index_file)
        for i, v in enumerate(item_names):
            self.items[v] = (index_index, i)

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        self._load_index("targets")
        self._load_index("documents")

    def _neighbors(self, v, n=5, index=0, names=False):
        """get a set of neighbors for a document"""

        if self.indexes[index] is None:
            return [], []
        get_nns = self.indexes[index].knnQueryBatch
        temp = get_nns(csr_matrix(v), n)
        nns, distances = temp[0][0], temp[0][1]
        if names:
            index_names = self.item_names[index]
            nns = [index_names[_] for _ in nns]
        return nns, distances

    def encode(self, doc):
        result, _ = self.encoder.encode(doc)
        return normalize_vec(result)

    def nearest_targets(self, v, n=5):
        return self._neighbors(v, n, index=0, names=True)

    def nearest_documents(self, v, n=5):
        return self._neighbors(v, n, index=1, names=True)

    def suggest_targets(self, v, n=5):
        """suggest nearest neighbors for a vector

        Arguments:
            v     list with float values
            n     integer, number of suggestions

        Returns:
            two lists:
            first list has with target ids
            second list has composite/weighted distances
        """

        v = csr_matrix(v)
        vlist = sparse_to_list(v)
        target_vector = self.data[0]
        doc_vector = self.data[1]

        # get direct distances from vector to targets
        nn0, dist0 = self._neighbors(v, n, index=0)
        target_dist = {i: d for i, d in zip(nn0, dist0)}
        target_data = {i: sparse_to_list(target_vector[i]) for i in nn0}
        # collect relevant documents
        nn1, dist1 = self._neighbors(v, n, index=1)
        doc_dist = {i: d for i, d in zip(nn1, dist1)}
        doc_data = {i: sparse_to_list(doc_vector[i]) for i in nn1}

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
                target_data[i_target] = sparse_to_list(target_vector[i_target])
                target_dist[i_target] = euc_dist(target_data[i_target], vlist)

        # compute weighted distances from vector to targets
        result = target_dist.copy()
        for i, d_v_i in doc_dist.items():
            i_data = doc_data[i]
            i_target_dist = doc_target_dist[i]
            for j in target_dist.keys():
                if j in i_target_dist:
                    d_i_j = i_target_dist[j]
                else:
                    d_i_j = euc_dist(i_data, target_data[j])
                result[j] += (d_v_i + d_i_j)/n

        result = sorted(result.items(), key=lambda x: x[1])
        suggestions = [self.item_names[0][i] for i, _ in result]
        distances = [float(d) for _, d in result]
        return suggestions, distances


class CrossmapAnnoyIndexer:
    """Indexing data for crossmap"""

    def __init__(self, settings, features=None):
        """create new indexer

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        self.settings = settings
        tokenizer = CrossmapTokenizer(settings)
        if features is not None:
            self.feature_map = {k: i for i, k in enumerate(features)}
        else:
            self.feature_map = feature_map(settings)
        self.encoder = CrossmapEncoder(self.feature_map, tokenizer)
        self.items = dict()
        self.item_names = []
        self.indexes = []
        self.index_files = []

    def clear(self):
        self.items = dict()
        self.item_names = []
        self.indexes = []
        self.index_files = []

    def _build_index(self, files, label=""):
        """builds an Annoy index using data from documents on disk"""

        if len(files) == 0:
            warning("Skipping build index for " + label + " - no data")
            self.indexes.append(None)
            self.index_files.append(None)
            self.item_names.append(None)
            return

        index_file = self.settings.annoy_file(label)
        items_file = self.settings.pickle_file(label + "-item-names")
        if exists(index_file) and exists(items_file):
            warning("Skipping build index for " + label + " - already exists")
            self._load_index(label)
            return

        info("Building index for " + label)
        index_index = len(self.indexes)
        items, item_names = self.encoder.documents(files)
        result = AnnoyIndex(len(self.feature_map), 'angular')
        for i in range(len(item_names)):
            result.add_item(i, items[i])
            self.items[item_names[i]] = (index_index, i)
        result.build(10)
        # record the index and items names
        self.item_names.append(item_names)
        self.indexes.append(result)
        self.index_files.append(index_file)
        # cache the index and item names
        result.save(index_file)
        write_obj(item_names, items_file)

    def build(self):
        """construct indexes from targets and other documents"""

        # build an index just for the targets, then just for documents
        settings = self.settings
        self.clear()
        self._build_index(settings.files("targets"), "targets")
        self._build_index(settings.files("documents"), "documents")

    def _load_index(self, label=""):
        index_file = self.settings.annoy_file(label)
        items_file = self.settings.pickle_file(label + "-item-names")
        index_index = len(self.indexes)
        if not exists(index_file):
            warning("Skipping loading index for " + label)
            self.indexes.append(None)
            self.index_files.append(None)
            self.item_names.append(None)
            return

        info("Loading index for " + label)
        annoy_index = AnnoyIndex(len(self.feature_map), "angular")
        annoy_index.load(index_file)
        self.indexes.append(annoy_index)
        item_names = read_obj(items_file)
        self.item_names.append(item_names)
        self.index_files.append(index_file)
        for i, v in enumerate(item_names):
            self.items[v] = (index_index, i)

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        self._load_index("targets")
        self._load_index("documents")

    def _neighbors(self, v, n=5, index=0):
        """get a set of neighbors for a document"""

        get_nns = self.indexes[index].get_nns_by_vector
        nns, distances = get_nns(v, n, include_distances=True)
        index_names = self.item_names[index]
        return [index_names[_] for _ in nns], distances

    def encode(self, doc):
        result, _ = self.encoder.encode(doc)
        return result

    def nearest_targets(self, v, n=5):
        return self._neighbors(v, n, index=0)

    def nearest_documents(self, v, n=5):
        return self._neighbors(v, n, index=1)

    def suggest_targets(self, v, n=5):
        """suggest nearest neighbors for a vector

        Arguments:
            v     list with float values
            n     integer, number of suggestions

        Returns:
            two lists:
            first list has with target ids
            second list has composite/weighted distances
        """

        indexes = self.indexes
        target_nns = indexes[0].get_nns_by_vector
        doc_nns = indexes[1].get_nns_by_vector
        target_vector = indexes[0].get_item_vector
        doc_vector = indexes[1].get_item_vector

        # get direct distances from vector to targets
        nn0, dist0 = target_nns(v, n, include_distances=True)
        target_dist = {i: d for i, d in zip(nn0, dist0)}
        target_data = {i: target_vector(i) for i in nn0}
        # collect relevant documents
        nn1, dist1 = doc_nns(v, n, include_distances=True)
        doc_dist = {i: d for i, d in zip(nn1, dist1)}
        doc_data = {i: doc_vector(i) for i in nn1}

        # record distances from docs to targets
        # (some docs may introduce new targets to consider)
        doc_target_dist = dict()
        for i_doc in nn1:
            i_doc_data = doc_data[i_doc]
            nn2, dist2 = target_nns(i_doc_data, n, include_distances=True)
            doc_target_dist[i_doc] = {j: d for j, d in zip(nn2, dist2)}
            for i_target in nn2:
                if i_target in target_dist:
                    continue
                target_data[i_target] = target_vector(i_target)
                target_dist[i_target] = euc_dist(target_data[i_target], v)

        # compute weighted distances from vector to targets
        result = target_dist.copy()
        for i, d_v_i in doc_dist.items():
            i_data = doc_data[i]
            i_target_dist = doc_target_dist[i]
            for j in target_dist.keys():
                if j in i_target_dist:
                    d_i_j = i_target_dist[j]
                else:
                    d_i_j = euc_dist(i_data, target_data[j])
                result[j] += (d_v_i + d_i_j)/n

        result = sorted(result.items(), key=lambda x: x[1])
        suggestions = [self.item_names[0][i] for i, _ in result]
        distances = [d for _, d in result]
        return suggestions, distances
