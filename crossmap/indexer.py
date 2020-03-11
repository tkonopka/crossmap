"""
Indexer of crossmap data for nearest-neighbor search
"""

import logging
import nmslib
from math import sqrt, floor
from os import remove
from os.path import exists
from logging import info, warning, error
from scipy.sparse import csr_matrix, vstack
from .db import CrossmapDB
from .tokenizer import CrossmapTokenizer
from .encoder import CrossmapEncoder
from .features import CrossmapFeatures
from .vectors import all_zero, sparse_to_dense
from .distance import euc_dist


# this removes the INFO messages from nmslib
logging.getLogger('nmslib').setLevel(logging.WARNING)

# special constant for maximal distance between normalized vectors
sqrt2 = sqrt(2.0)
almost_sqrt2 = floor(sqrt2*1e7)/1e7


class CrossmapIndexer:
    """Indexing data for crossmap"""

    def __init__(self, settings):
        """initialize indexes and their links with the crossmap db

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        self.settings = settings
        features = CrossmapFeatures(settings)
        tokenizer = CrossmapTokenizer(settings)
        self.db = CrossmapDB(self.settings.db_file())
        self.db.build()
        self.encoder = CrossmapEncoder(features.map, tokenizer)
        self.indexes = dict()
        self.index_files = dict()
        # cache holding string identifiers for items in the db
        self.item_ids = dict()

    def clear(self):
        self.indexes = dict()
        self.index_files = dict()

    def update(self, dataset, doc, id, rebuild=True):
        """augment an existing dataset with a new item

        :param dataset: string, dataset identifier
        :param doc: dict with item data_pos, data_neg, etc
        :param id: string, identifier for the new item
        :param rebuild: boolean, True to rebuild index structures, False to skip
        :return: integer index for the new data item
        """

        if self.db.has_id(dataset, id):
            raise Exception("item id already exists: " + str(id))

        titles = None
        if "title" in doc:
            titles = [doc["title"]]
        v = self.encoder.document(doc)
        size = self.db.dataset_size(dataset)
        idxs = self.db.add_data(dataset, [v], [id], titles, indexes=[size])
        if rebuild:
            self.rebuild_index(dataset)
        return idxs[0]

    def _build_data(self, files, dataset):
        """transfer data from files into a db table

        :param files: list with file paths
        :param dataset: string, label for dataset
        :return:
        """

        size = self.db.dataset_size(dataset)
        if size > 0:
            warning("Skipping data transfer: " + dataset)
            return

        info("Transferring data: " + dataset)
        batch_size = self.settings.logging.progress

        # internal helper to save a batch of data into the index and db
        def add_batch(items, ids, titles, offset):
            if len(items) == 0:
                return 0
            self.db.add_data(dataset, items, ids, titles=titles,
                             indexes=[offset+_ for _ in range(len(items))])
            return len(items)

        items, ids, titles, offset = [], [], [], 0
        for _tokens, _id, _title in self.encoder.documents(files):
            if all_zero(_tokens.toarray()[0]):
                warning("Skipping item: " + str(_id))
                continue
            items.append(_tokens)
            ids.append(_id)
            titles.append(_title)
            if len(items) >= batch_size:
                offset += add_batch(items, ids, titles, offset)
                info("Progress: " + str(offset))
                items, ids, titles = [], [], []
        # force a batch save at the end of reading data
        offset += add_batch(items, ids, titles, offset)

        summary_fun = warning if offset == 0 else info
        summary_fun("Number of items: " + str(offset))

    def _build_index(self, dataset):
        """builds an Annoy index using data from documents on disk"""

        index_file = self.settings.index_file(dataset)
        if exists(index_file):
            warning("Skipping search index build: " + dataset)
            self._load_index(dataset)
            return

        info("Building search index: " + dataset)
        batch_size = self.settings.logging.progress
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        items, idxs, num_items = [], [], 0
        for row in self.db.all_data(dataset):
            items.append(row["data"])
            idxs.append(row["idx"])
            if len(items) >= batch_size:
                num_items += batch_size
                info("Progress: " + str(num_items))
                result.addDataPointBatch(vstack(items), idxs)
                items, idxs = [], []
        if len(items) > 0:
            result.addDataPointBatch(vstack(items), idxs)

        build_quality = self.settings.indexing.build_quality
        result.createIndex(index_params={"efConstruction": build_quality},
                           print_progress=False)
        self.indexes[dataset] = result
        self.index_files[dataset] = index_file
        result.saveIndex(index_file, save_data=True)

    def rebuild_index(self, dataset):
        """delete an exsting index and force a rebuild

        :param dataset: string, name of dataset to rebuild
        """

        index_file = self.settings.index_file(dataset)
        if exists(index_file):
            remove(index_file)
        self._build_index(dataset)

    def build(self):
        """construct indexes from targets and other documents"""

        # build an index just for the targets, then just for documents
        settings = self.settings
        self.clear()
        for dataset in self.settings.data_files.keys():
            if dataset not in self.db.datasets:
                self.db.register_dataset(dataset)
        for dataset, filepath in settings.data_files.items():
            self._build_data(filepath, dataset)
            self._build_index(dataset)
        self.db.get_feature_map()

    def _load_index(self, dataset):
        """retrieve a nmslib index from disk into memory

        :param dataset: string, label identifier for the index
        :return: nothing, the internal state changes
        """
        index_file = self.settings.index_file(dataset)
        if not exists(index_file):
            error("Skipping loading search index: " + dataset)
            return

        info("Loading search index: " + dataset)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.loadIndex(index_file, load_data=True)
        search_quality = self.settings.indexing.search_quality
        result.setQueryTimeParams({"efSearch": search_quality})
        self.indexes[dataset] = result
        self.index_files[dataset] = index_file

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        for label in self.db.datasets.keys():
            self._load_index(label)

    def _neighbors(self, v, dataset, n=5, names=False):
        """get a set of neighbors for a document"""

        if dataset not in self.indexes:
            return [], []
        get_nns = self.indexes[dataset].knnQueryBatch
        temp = get_nns(csr_matrix(v), n)
        nns, distances = temp[0][0], temp[0][1]
        nns = [int(_) for _ in nns]
        if names:
            nns_map = self.db.ids(dataset, nns)
            nns = [nns_map[_] for _ in nns]
        return nns, distances

    def encode_document(self, doc):
        return self.encoder.document(doc)

    def nearest(self, v, label, n):
        """look up nearest neighbors for a data vector

        :param v: csr matrix with data vector
        :param label: string, name of index
        :param n: integer, number of neighbors
        :return: a list of ids for nearest neighbors, a list with distances
        """
        return self._neighbors(v, label, n, names=True)

    def _load_item_ids(self, dataset):
        """cache string identifiers"""

        if dataset not in self.item_ids:
            self.item_ids[dataset] = self.db.all_ids(dataset)

    def distances(self, v, dataset, ids=[]):
        """get distances between a dense vector and items in the db"""

        v_dense = sparse_to_dense(v)
        target_data = self.db.get_data(dataset, ids=ids)
        distances, ids = [], []
        for d in target_data:
            ids.append(d["id"])
            d_dense = sparse_to_dense(d["data"])
            distances.append(euc_dist(v_dense, d_dense)/sqrt2)
        return distances, ids

    def suggest(self, v, dataset, n=5):
        """suggest nearest neighbors using a composite algorithm

        :param v:
        :param dataset: string or integer, name of index/dataset
        :param n: integer, number of nearest neighbors
        :return: a list of items ids, a list of composite distances
        """

        self._load_item_ids(dataset)
        v = csr_matrix(v)
        neighbors, distances = self._neighbors(v, dataset, n)
        item_ids = self.item_ids[dataset]
        suggestions = [item_ids[_] for _ in neighbors]
        # Two entirely different unit vectors have a distance of sqrt(2)
        # The division below transforms output to [0, 1]
        distances = [float(_)/sqrt2 for _ in distances]
        return suggestions, distances

    @property
    def valid(self):
        """summarizes if the object was initialized correctly"""

        if len(self.indexes) == 0:
            return False
        if self.encoder.feature_map is None:
            return False
        return len(self.encoder.feature_map) > 0

    def __str__(self):
        """short description of the indexer structure"""

        result = ["Indexer",
                  "Feature map: \t" + str(len(self.encoder.feature_map)),
                  "Num. Indexes:\t" + str(len(self.indexes))]
        return "\n".join(result)

