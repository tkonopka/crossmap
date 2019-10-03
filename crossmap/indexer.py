"""Indexer of crossmap data for NN search
"""

import logging
import nmslib
from os.path import exists
from logging import info, warning, error
from scipy.sparse import csr_matrix, vstack
from .features import feature_map, feature_dict_map
from .db import CrossmapDB
from .tokens import CrossmapTokenizer
from .encoder import CrossmapEncoder
from .vectors import all_zero, sparse_to_dense
from .distance import euc_dist
from .tools import read_dict


# this removes the INFO messages from nmslib
logging.getLogger('nmslib').setLevel(logging.WARNING)


class CrossmapIndexer:
    """Indexing data for crossmap"""

    def __init__(self, settings, features=None):
        """initialize indexes and their links with the crossmap db

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        self.settings = settings
        tokenizer = CrossmapTokenizer(settings)
        self.db = CrossmapDB(self.settings.db_file())
        self.db.build()
        self.feature_map = self._init_features(features)
        if len(self.feature_map) == 0:
            error("feature map is empty")
        self.encoder = CrossmapEncoder(self.feature_map, tokenizer)
        self.indexes = dict()
        self.index_files = dict()
        # cache holding string identifiers for items in the db
        self.item_ids = dict()

    def _init_features(self, features):
        """determine the feature_map compoent from db, file, or from scratch"""

        if self.db.count_features() == 0:
            features_file = self.settings.features.map_file
            if features is None and features_file is not None:
                info("reading features from prepared dictionary")
                features = read_dict(features_file, id_col="id",
                                     value_col="weight", value_fun=float)
            if features is None:
                result = feature_map(self.settings)
            else:
                result = feature_dict_map(self.settings, features)
            self.db.set_feature_map(result)
        else:
            if features is not None:
                warning("features in constructor will be ignored")
            result= self.db.get_feature_map()

        return result

    def clear(self):
        self.indexes = dict()
        self.index_files = dict()

    def _build_index(self, files, label, batch_size=100000):
        """builds an Annoy index using data from documents on disk"""

        index_file = self.settings.index_file(label)
        if exists(index_file):
            warning("Skipping build index for " + label + " - already exists")
            self._load_index(label)
            return
        info("Building data index for " + label)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        items, ids, titles, offset = [], [], [], 0

        # internal helper to save a batch of data into the index and db
        def add_batch(items, ids, titles, offset):
            if len(items) == 0:
                return 0
            local_indexes = [offset+_ for _ in list(range(len(items)))]
            self.db.add_data(label, items, ids, titles=titles,
                             indexes=local_indexes)
            result.addDataPointBatch(vstack(items), local_indexes)
            return len(items)

        num_items = 0
        for _tokens, _id, _title in self.encoder.documents(files):
            if all_zero(_tokens.toarray()[0]):
                warning("Skipping item - null vector for id " + str(_id))
                continue
            items.append(_tokens)
            ids.append(_id)
            titles.append(_title)
            if len(items) >= batch_size:
                num_items += batch_size
                info("Progress: " + str(num_items))
                offset += add_batch(items, ids, titles, offset)
                items, ids, titles = [], [], []
        # force a batch save at the end of reading data
        offset += add_batch(items, ids, titles, offset)

        if offset == 0:
            logfun = warning if label == "documents" else error
            logfun("No content for " + label)
            return
        info("Total number of items: "+str(offset))

        result.createIndex(print_progress=False)
        self.indexes[label] = result
        self.index_files[label] = index_file
        result.saveIndex(index_file, save_data=True)

    def build(self):
        """construct indexes from targets and other documents"""

        # build an index just for the targets, then just for documents
        settings = self.settings
        self.clear()
        for label in self.settings.data_files.keys():
            if label not in self.db.datasets:
                self.db.register_dataset(label)
        for label, filepath in settings.data_files.items():
            self._build_index(filepath, label)
        self.db.count_features()

    def _load_index(self, label):
        """retrieve a nmslib index from disk into memory

        :param label: string, label identifier for the index
        :return: nothing, the internal state changes
        """
        index_file = self.settings.index_file(label)
        if not exists(index_file):
            error("Skipping loading index for " + label)
            return

        info("Loading index for " + label)
        result = nmslib.init(method="hnsw", space="l2_sparse",
                             data_type=nmslib.DataType.SPARSE_VECTOR)
        result.loadIndex(index_file, load_data=True)
        self.indexes[label] = result
        self.index_files[label] = index_file

    def load(self):
        """Load indexes from disk files"""

        self.clear()
        for label in self.db.datasets.keys():
            self._load_index(label)

    def _neighbors(self, v, label, n=5, names=False):
        """get a set of neighbors for a document"""

        if label not in self.indexes:
            return [], []
        get_nns = self.indexes[label].knnQueryBatch
        temp = get_nns(csr_matrix(v), n)
        nns, distances = temp[0][0], temp[0][1]
        nns = [int(_) for _ in nns]
        if names:
            nns = self.db.ids(label, nns)
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

    def _load_item_ids(self, label):
        """cache string identifiers """

        if label not in self.item_ids:
            self.item_ids[label] = self.db.all_ids(label)

    def suggest(self, v, label, n=5, aux=None):
        """suggest nearest neighbors using a composite algorithm

        :param v:
        :param label: string, name of index of integer
        :param n: integer, number of nearest neighbors
        :param aux: dictionary linking index labels to nearest neighbors
        :return: a list of items ids, a list of composite distances
        """

        self._load_item_ids(label)
        v = csr_matrix(v)
        vlist = sparse_to_dense(v)
        db, _n = self.db, self._neighbors
        aux = aux or dict()

        # get direct distances from vector to targets
        nn0, dist0 = _n(v, label, n)
        target_dist = {i: d for i, d in zip(nn0, dist0)}
        #print("target_dist "+str(target_dist))
        target_data = dict()
        hits_targets = db.get_data(label, idxs=nn0)
        for _, val in enumerate(hits_targets):
            target_data[val["idx"]] = sparse_to_dense(val["data"])
        # collect relevant auxiliary documents
        # nn1 - integer indexes in the auxiliary datasets
        # dist1 - distances from v to the auxiliary items
        # doc1 - dict of arrays with sparse vectors
        # data1 - dict of dicts holding dense vectors
        nn1, dist1, doc1, data1 = dict(), dict(), dict(), dict()
        for aux_label, aux_n in aux.items():
            #print("querying aux label: "+aux_label)
            nn1[aux_label], dist1[aux_label] = _n(v, aux_label, aux_n)
            doc1[aux_label] = db.get_data(aux_label, idxs=nn1[aux_label])
            data1[aux_label] = dict()
            for _, val in enumerate(doc1[aux_label]):
                data1[aux_label][val["idx"]] = sparse_to_dense(val["data"])
        #print("nn1 " + str(nn1))
        #print("dist1 " + str(dist1))
        #print("doc1 " + str(doc1))
        #print("data1 " + str(data1))

        # record distances from auxiliary documents to targets
        # (some docs may introduce new targets to consider)
        doc_target_dist = dict()
        for aux_label in nn1.keys():
            for doc in nn1[aux_label]:
                i_data = data1[aux_label][doc]
                nn2, dist2 = _n(i_data, label, n)
                doc_target_dist[aux_label+str(doc)] = dict()
                for j, d in zip(nn2, dist2):
                    doc_target_dist[aux_label+str(doc)][j] = d
                for target in nn2:
                    if target in target_dist:
                        continue
                    temp = db.get_data(label, idxs=[target])
                    i_target_data = db.get_data(label, idxs=[target])[0]
                    target_data[target] = sparse_to_dense(i_target_data["data"])
                    target_dist[target] = euc_dist(target_data[target], vlist)

        #print("target_dist "+str(target_dist))
        #print("doc target dist "+str(doc_target_dist))
        # compute weighted distances from vector to targets
        result = target_dist.copy()
        n_doc = sum([_ for _ in aux.values()])
        #print("n_doc "+str(n_doc))
        for aux_label in nn1.keys():
            for i, d_v_i in zip(nn1[aux_label], dist1[aux_label]):
                i_data = data1[aux_label][i]
                i_target_dist = doc_target_dist[aux_label+str(i)]
                for j in target_dist.keys():
                    if j in i_target_dist:
                        d_i_j = i_target_dist[j]
                    else:
                        d_i_j = euc_dist(i_data, target_data[j])
                    result[j] += (d_v_i + d_i_j)/n_doc

        result = sorted(result.items(), key=lambda x: x[1])
        target_ids = self.item_ids[label]
        suggestions = [target_ids[i] for i, _ in result]
        distances = [float(d) for _, d in result]
        return suggestions, distances

    @property
    def valid(self):
        """summarizes if the object was initialized correctly"""

        if len(self.indexes) == 0:
            return False
        if self.feature_map is None:
            return False
        return len(self.feature_map) > 0

    def __str__(self):
        """short description of the indexer structure"""

        result = ["Indexer",
                  "Feature map: \t" + str(len(self.feature_map)),
                  "Num. Indexes:\t" + str(len(self.indexes))]
        return "\n".join(result)

