"""Indexer of crossmap data for NN search
"""

from os.path import exists
from logging import info, warning
from annoy import AnnoyIndex
from .feature_map import feature_map
from .tokens import CrossmapTokenizer
from .tools import read_obj, write_obj
from .data import CrossmapData


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
        self.builder = CrossmapData(self.feature_map, tokenizer)
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
            warning("Skipping build index for " + label)
            self.indexes.append(None)
            self.index_files.append(None)
            self.item_names.append(None)
            return

        info("Building index for " + label)
        index_file = self.settings.index_file(label)
        items_file = self.settings.pickle_file(label + "-item-names")
        index_index = len(self.indexes)
        items, item_names = self.builder.documents(files)
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
        index_file = self.settings.index_file(label)
        items_file = self.settings.pickle_file(label + "-item-names")
        index_index = len(self.indexes)
        if not exists(index_file):
            warning("Skipping loading index for " + label)
            self.indexes.append(None)
            self.index_files.append(None)
            self.item_names.append(None)
            return

        annoy_index = AnnoyIndex(len(self.feature_map), "angular")
        annoy_index.load(index_file)
        self.indexes.append(annoy_index)
        item_names = read_obj(items_file)
        self.item_names.append(item_names)
        for i, v in enumerate(item_names):
            self.items[v] = (index_index, i)

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        self._load_index("targets")
        self._load_index("documents")

    def _neighbors(self, doc, n=5, index=0):
        """get a set of neighbors for a document"""

        doc_data, doc_name = self.builder.single(doc)
        get_nns = self.indexes[index].get_nns_by_vector
        nns, distances = get_nns(doc_data, n, include_distances=True)
        index_names = self.item_names[index]
        return [index_names[_] for _ in nns], distances

    def nearest_targets(self, doc, n=5):
        return self._neighbors(doc, n, index=0)

    def nearest_docs(self, doc, n=5):
        return self._neighbors(doc, n, index=1)
