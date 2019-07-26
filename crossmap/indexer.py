"""Indexer of crossmap data for NN search
"""

from os.path import exists
from logging import info
from annoy import AnnoyIndex
from .feature_map import feature_map
from .tokens import CrossmapTokenizer
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

    def _build_index(self, files, label=""):
        """builds an Annoy index using data from documents on disk"""

        index_index = len(self.indexes)
        items, item_names = self.builder.documents(files)
        result = AnnoyIndex(len(self.feature_map), 'angular')
        for i in range(len(item_names)):
            result.add_item(i, items[i])
            self.items[item_names[i]] = (index_index, i)
        self.item_names.append(item_names)
        result.build(10)
        index_file = self.settings.index_file(label)
        result.save(index_file)
        # record the index and items names
        self.indexes.append(result)
        self.index_files.append(index_file)

    def build(self):
        """construct indexes from """

        # build an index just for the targets, then just for documents
        settings = self.settings
        info("Building index for targets")
        self._build_index(settings.files("targets"), "targets")
        info("Building index for documents")
        self._build_index(settings.files("documents"), "documents")

    def _load_index(self, label=""):
        index_file = self.settings.index_file(label)
        if not exists(index_file):
            return None
        annoy_index = AnnoyIndex(len(self.feature_map), "angular")
        annoy_index.load(index_file)
        return annoy_index

    def load(self):
        """Attempt to load indexes from disk files"""

        self.indexes = []
        self.indexes.append(self._load_index("targets"))
        self.indexes.append(self._load_index("documents"))
        if self.indexes[0] is None and self.indexes[1] is None:
            return False
        return True

    def _neighbors(self, doc, n=5, index=0):
        """get a set of neighbors for a document"""

        doc_data, doc_name = self.builder.single(doc)
        indx = self.indexes[index]
        return indx.get_nns_by_vector(doc_data, n, include_distances=True)

    def nearest_targets(self, doc, n=5):
        return self._neighbors(doc, n, index=0)

    def nearest_docs(self, doc, n=5):
        return self._neighbors(doc, n, index=1)
