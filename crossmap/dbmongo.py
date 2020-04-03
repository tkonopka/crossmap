"""
Interface to a specialized db (implemented as monogodb)
"""

from pymongo import MongoClient
from functools import wraps
from logging import info, warning, error
from scipy.sparse import csr_matrix
from .csr import csr_to_bytes, bytes_to_csr, bytes_to_arrays
from .cache import CrossmapCache
from .subsettings import CrossmapCacheSettings


# collections used in each CrossmapMongoDB instance
crossmap_collection_types = {"features", "datasets", "data", "counts"}


def valid_dataset(f):
    """decorator that formats dataset identifier into a valid integer"""

    @wraps(f)
    def wrapped(self, dataset, *args, **kw):
        if type(dataset) is str:
            if dataset not in self.datasets:
                raise Exception("Invalid dataset: "+str(dataset))
            dataset = self.datasets[dataset]
        elif type(dataset) is int:
            if dataset not in set(self.datasets.values()):
                raise Exception("Invalid dataset: "+str(dataset))
        else:
            raise Exception("Invalid dataset identifier type")
        return f(self, dataset, *args, **kw)

    return wrapped


class CrossmapMongoDB:
    """Management of a DB for features and data vectors"""

    def __init__(self, settings, cache_settings=None):
        """sets up a connection to a db and defines settings"""

        dbname = settings.name
        #print(str(settings.server))
        client = MongoClient(host=settings.server.db_host,
                             port=settings.server.db_port,
                             username="crossmap",
                             password="crossmap")
        # set up connection to the db, and to collections
        info("Creating database")
        self._db = client[dbname]
        self._features = self._db["features"]
        self._datasets = self._db["datasets"]
        self._data = self._db["data"]
        self._counts = self._db["counts"]

        # set up cache objects (uses sloppy cache by default)
        self.n_features = self._features.count_documents({})
        self.datasets = self._dataset_labels()
        if cache_settings is None:
            cache_settings = CrossmapCacheSettings()
        self.counts_cache = CrossmapCache(cache_settings.counts)
        self.titles_cache = CrossmapCache(cache_settings.titles)
        self.data_cache = CrossmapCache(cache_settings.data)

    def _dataset_labels(self):
        """read dataset labels from db

        :return: dict with mapping from label to integer identifier
        """

        result = dict()
        for x in self._datasets.find():
            result[x["label"]] = x["dataset"]
        return result

    @valid_dataset
    def _clear_table(self, dataset, collection="counts"):
        """remove all content from a table

        :param dataset: string, dataset identifier
        :param collection: string, name of table, use "data" or "counts"
        """

        if collection not in crossmap_collection_types:
            raise Exception("clearing not supported for: " + collection)
        self._db[collection].delete_many({"dataset": dataset})

    @valid_dataset
    def count_rows(self, dataset, collection="data"):
        """generic function to count rows in any table within db

        :param dataset: string, dataset identifier
        :param collection: string, one of "counts" or "data"
        :return: integer number of rows
        """

        if collection not in crossmap_collection_types:
            return 0
        return self._db[collection].count_documents({"dataset": dataset})

    def build(self):
        """this exists for consistency with sqlite db"""
        pass

    def rebuild(self):
        """empty the contents of the database tables"""

        warning("Removing existing database")
        for x in crossmap_collection_types:
            self._db[x].delete_many({})

    def validate_dataset_label(self, label):
        """evaluates whether a label is allowed for a dataset

        A good dataset label must be composed of alphanumeric characters
        or underscores.

        :param label: string, candidate dataset identifier
        :return: 1 if label is OK for a new dataset, 0 if label already exists,
            -1 if label is not alphanumeric
        """

        if type(label) is not str:
            return -1
        for x in label:
            if not (x == "_" or x.isalnum()):
                return -1
        if label.startswith("_") or label.endswith("_"):
            return -1
        self.datasets = self._dataset_labels()
        return int(label not in self.datasets)

    def register_dataset(self, label, title=""):
        """register a new dataset label

        :param label: string, a new data set label
        :param title: string, an additional descriptor for the dataset
        :return: nothing, changes are made to the db
        """

        self.datasets = self._dataset_labels()
        if label in self.datasets:
            error("dataset label already exists")
            return
        self._datasets.insert_one({"dataset": len(self.datasets),
                                   "label": label,
                                   "title": title})
        self.datasets = self._dataset_labels()

    @valid_dataset
    def dataset_size(self, dataset):
        """get current number of rows in data table for a dataset

        :param dataset: string or int, identifier for a dataset
        :return: integer, number of data rows associated to a dataset
        """

        return self._data.count_documents({"dataset": dataset})

    def _index(self, collection="data", types=("id", "idx")):
        """create indexes one db collection"""

        for x in types:
            self._db[collection].create_index({"dataset": 1, x: 1})

    def index(self, collection):
        """create indexes on existing tables in the database"""

        info("Indexing " + collection)
        if collection == "data":
            self._data.create_index([("dataset", 1), ("id", 1)])
            self._data.create_index([("dataset", 1), ("idx", 1)])
        elif collection == "counts":
            self._counts.create_index([("dataset", 1), ("idx", 1)])

    def get_feature_map(self):
        """construct a feature map"""

        result = dict()
        for row in self._features.find({}):
            result[row["id"]] = (row["idx"], row["weight"])
        return result

    def set_feature_map(self, feature_map):
        """add content into the feature map table"""

        feature_list = []
        for k, v in feature_map.items():
            feature_list.append(dict(id=k, idx=v[0], weight=v[1]))
        self._features.delete_many({})
        self._features.insert_many(feature_list)
        self.n_features = len(feature_map)

    @valid_dataset
    def set_counts(self, dataset, data):
        """insert rows into the counts table.

        (This will remove existing counts rows associated with a dataset
        and set the new data instead)

        :param dataset: string or int, identifier for a dataset
        :param data: list with rows to insert
        """

        self.counts_cache.clear()
        self._clear_table(dataset, "counts")
        data_array = []
        for i in range(len(data)):
            i_bytes = csr_to_bytes(data[i])
            data_array.append({"dataset": dataset, "idx": i, "data": i_bytes})
        self._counts.insert_many(data_array)

    @valid_dataset
    def update_counts(self, dataset, data):
        """change existing rows of counts

        :param dataset: string or int, identifier for a dataset
        :param data: dict mapping indexes to csr_matrices
        """

        self.counts_cache.clear()
        for i, v in data.items():
            i_bytes = csr_to_bytes(v)
            self._counts.update_one({"dataset": dataset, "idx": i},
                                    {"$set": {"data": i_bytes}})

    @valid_dataset
    def add_data(self, dataset, data, ids, titles=None, indexes=None):
        """insert rows into the 'data' table

        :param dataset: string or int, dataset identifier
        :param data: list with vectors
        :param ids: list with string-like identifiers
        :param titles: list with string-like descriptions
        :param indexes: list with integer identifiers
        :return: list of indexes used for the new documents
        """

        self.data_cache.clear()
        self.titles_cache.clear()
        if indexes is None:
            current_size = self.dataset_size(dataset)
            indexes = [current_size + _ for _ in range(len(ids))]
        if titles is None:
            titles = [""]*len(ids)

        data_array = []
        for i in range(len(ids)):
            data_array.append({"dataset": dataset, "id": ids[i],
                               "idx": indexes[i], "title": titles[i],
                               "data": csr_to_bytes(data[i])})
        self._data.insert_many(data_array)
        return indexes

    @valid_dataset
    def get_counts_arrays(self, dataset, idxs):
        """retrieve information from counts tables.

        Uses cache when available. Fetches remaining items from db.

        :param dataset: string or int, dataset identifier
        :param idxs: list of integers
        :return: dictionary mapping indexes to arrays with sparse data,
            sparse indices, and a row sum
        """

        result, missing = self.counts_cache.get(dataset, idxs)
        if len(missing) == 0:
            return result
        find = self._counts.find
        for row in find({"dataset": dataset, "idx": {"$in": missing}},
                        {"_id": 0, "idx": 1, "data": 1}):
            row_data = bytes_to_arrays(row["data"])
            idx = row["idx"]
            result[idx] = row_data
            self.counts_cache.set(dataset, idx, row_data)
        return result

    @valid_dataset
    def get_counts(self, dataset, idxs):
        """retrieve information from counts tables.

        Uses cache when available. Fetches remaining items from db.

        Note there is a related function get_counts_arrays, which
        retrieves arrays with a sum instead of csr_matrix objects.
        That function is faster and should be preferred.

        :param dataset: string or int, dataset identifier
        :param idxs: list of integers
        :return: dictionary mapping indexes to count csr_matrix objects
        """

        shape = (1, self.n_features)
        pre_result = self.get_counts_arrays(dataset, idxs)
        result = dict()
        for k, v in pre_result.items():
            result[k] = csr_matrix((v[0], v[1], (0, len(v[1]))), shape=shape)
        return result

    @valid_dataset
    def sparsity(self, dataset, table="counts"):
        """compute sparsity values for all items in data or counts tables

        :param dataset: string or int, identifier for a dataset
        :param table: string, one 'counts' or 'data'
        :return: list of sparsity values for all relevant rows in the table
        """

        if table not in set(["data", "counts"]):
            raise Exception("invalid table")
        result = []
        n_features = self.n_features
        for row in self._db[table].find({"dataset": dataset}):
            v = bytes_to_csr(row["data"], n_features)
            result.append(len(v.indices) / n_features)
        return result

    @valid_dataset
    def get_data(self, dataset, idxs=None, ids=None):
        """retrieve objects from db

        Note: one of ids or idx must be specified other than None

        :param dataset: string or int, string identifier for a dataset
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: list with content of database table
        """

        # get dimensions of feature vector
        if self.n_features is None:
            self.n_features = len(self.get_feature_map())
        n_features = self.n_features
        # determine whether to query by test id or numeric indexes
        queries, column = idxs, "idx"
        if ids is not None:
            queries, column = ids, "id"
        if queries is None or len(queries) == 0:
            return []
        # attempt to get results from cache
        result, missing = self.data_cache.get(dataset, queries)
        result = [v for v in result.values()]
        if len(missing) == 0:
            return result
        # perform queries to fill in remaining items
        find = self._data.find
        for row in find({"dataset": dataset, column: {"$in": missing}},
                        {"id": 1, "idx": 1, "data": 1, "_id": 0}):
            rowdict = dict(id=row["id"], idx=row["idx"],
                           data=bytes_to_csr(row["data"], n_features))
            result.append(rowdict)
            self.data_cache.set(dataset, row[column], rowdict)
        return result

    @valid_dataset
    def all_data(self, dataset):
        """generator for data rows for a specific dataset

        :param dataset: string or int, dataset identifier
        :return: dict with data entries
        """

        n_features = self.n_features
        for row in self._data.find({"dataset": dataset}):
            result = dict(id=row["id"], idx=row["idx"],
                          data=bytes_to_csr(row["data"], n_features))
            yield result

    @valid_dataset
    def get_titles(self, dataset, idxs=None, ids=None):
        """retrieve information from db from targets or documents

        (This might be used from a user-interface, so must support
        querying by ids as well as by idxs)

        :param dataset or int: string identifier for a dataset
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: dictionary mapping ids to titles
        """

        queries, column = idxs, "idx"
        if ids is not None:
            queries, column = ids, "id"
        # attempt to get results from cache
        result, missing = self.titles_cache.get(dataset, queries)
        if len(missing) == 0:
            return result
        # fetch the rest from the db
        find = self._data.find
        for row in find({"dataset": dataset, column: {"$in": missing}},
                        {"_id": 0, "id": 1, "idx": 1, "title": 1}):
            result[row[column]] = row["title"]
            self.titles_cache.set(dataset, row[column], row["title"])
        return result

    @valid_dataset
    def ids(self, dataset, idxs):
        """convert integer indexes to string ids

        :param dataset: string or int, identifier for a table
        :param idxs: iterable with numeric indexes. This function only supports
            small vectors of indexes.
        :return: dict mapping elements of idxs into string ids
        """

        if len(idxs) == 0:
            return dict()
        result = dict()
        for row in self._data.find({"dataset": dataset, "idx": {"$in": idxs}},
                                   {"_id": 0, "id": 1, "idx": 1}):
            result[row["idx"]] = row["id"]
        return result

    @valid_dataset
    def has_id(self, dataset, id):
        """check if database has an item with specified string identifier

        (Used before manual insertion of a new item, to avoid nonunique ids)

        :param dataset: string, dataset identifier
        :param id: string identifier to query
        :return: boolean
        """

        result = self._data.find_one({"dataset": dataset, "id": id},
                                     {"_id": 0, "id": 1})
        return result is not None

    @valid_dataset
    def all_ids(self, dataset):
        """get all ids associated with a dataset

        :param dataset: string or int, indicating to query targets or documents
        :return: list with ids corresponding to the dataset
        """

        n_rows = self._data.count_documents({"dataset": dataset})
        result = [None]*n_rows
        for row in self._data.find({"dataset": dataset}, {"idx": 1, "id": 1}):
            result[row["idx"]] = row["id"]
        return result
