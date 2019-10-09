"""
Interface to a specialized db (implemented as sqlite)
"""

import sqlite3
from functools import wraps
from logging import info, warning, error
from os.path import exists
from os import remove
from .csr import csr_to_bytes, bytes_to_csr
from .cache import CrossmapCache
from .subsettings import CrossmapCacheSettings


def get_conn(dbfile, timeout=5000):
    """get a connection to a databse"""
    conn = sqlite3.connect(dbfile, timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


# categorization of column names by field type
_text_cols = {"id", "title", "label"}
_int_cols = {"idx", "dataset"}
_real_cols = {"weight"}
_blob_cols = {"data"}


def columns_sql(colnames):
    """construct a partial sql command with column names

    :param colnames: list with strings
    :return: one string with a partial sql
    """

    result = []
    for x in colnames:
        if x in _text_cols:
            result.append(x + " TEXT")
        elif x in _int_cols:
            result.append(x + " INTEGER")
        elif x in _real_cols:
            result.append(x + " REAL")
        elif x in _blob_cols:
            result.append(x + " BLOB")
        else:
            raise Exception("invalid columns name")
    return "(" + ", ".join(result) + ")"


crossmap_table_names = {"features", "datasets", "data", "counts"}


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


class CrossmapDB:
    """Management of a DB for features and data vectors"""

    def __init__(self, db_file, cache_settings=None):
        """sets up path to db, operations performed via functions"""

        self.db_file = db_file
        self.n_features = None
        self.datasets = self._datasets()
        # set up cache objects (uses sloppy cache by default)
        if cache_settings is None:
            cache_settings = CrossmapCacheSettings()
        self.counts_cache = CrossmapCache(cache_settings.counts)
        self.titles_cache = CrossmapCache(cache_settings.titles)
        self.data_cache = CrossmapCache(cache_settings.data)

    def _datasets(self):
        """read dataset labels from db

        :return: dict with mapping from label to integer identifier
        """

        result = dict()
        if not exists(self.db_file):
            return result
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            c.execute("SELECT dataset, label FROM datasets")
            for row in c:
                result[row["label"]] = row["dataset"]
        return result

    @valid_dataset
    def _clear_table(self, dataset, table="counts"):
        """remove all content from a table

        :param dataset: string, dataset identifier
        :param table: string, name of table, use "data" or "counts"
        """

        if table not in crossmap_table_names:
            raise Exception("clearing not supported for: " + table)
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            sql = "DELETE FROM " + table + " WHERE dataset=?"
            c.execute(sql, (dataset,))
            conn.commit()

    @valid_dataset
    def count_rows(self, dataset, table="data"):
        """generic function to count rows in any table within db

        :param dataset: string, dataset identifier
        :param table: string, one of "counts" or "data"
        :return: integer number of rows
        """

        if table not in crossmap_table_names:
            return 0
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            sql = "SELECT COUNT(*) FROM " + table + " WHERE dataset=?"
            result = c.execute(sql, (dataset, )).fetchone()[0]
        return result

    def build(self, reset=False):
        """create a database with empty tables

        :param datasets: labels for data tables
        :param reset: boolean, set True to remove existing db and recreate
        :return:
        """

        if exists(self.db_file):
            if not reset:
                return
            warning("Removing existing database")
            remove(self.db_file)

        cols_features = columns_sql(("idx", "id", "weight"))
        cols_datasets = columns_sql(("dataset", "label", "title"))
        cols_data = columns_sql(("dataset", "idx", "id", "title", "data"))
        cols_counts = columns_sql(("dataset", "idx", "data"))

        info("Creating database")
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE features " + cols_features)
            cur.execute("CREATE TABLE datasets " + cols_datasets)
            cur.execute("CREATE TABLE data" + cols_data)
            cur.execute("CREATE TABLE counts" + cols_counts)
            conn.commit()

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
        self.datasets = self._datasets()
        return int(label not in self.datasets)

    def register_dataset(self, label, title=""):
        """register a new dataset label

        :param label: string, a new data set label
        :param title: string, an additional descriptor for the dataset
        :return: nothing, changes are made to the db
        """

        self.datasets = self._datasets()
        if label in self.datasets:
            error("dataset label already exists")
            return

        s = "INSERT INTO datasets (dataset, label, title) VALUES (?, ?, ?);"
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(s, [(len(self.datasets), label, title)])
            self.datasets[label] = len(self.datasets)
            conn.commit()

    @valid_dataset
    def dataset_size(self, dataset):
        """get current number of rows in data table for a dataset

        :param dataset: string or int, identifier for a dataset
        :return: integer, number of data rows associated to a dataset
        """

        with get_conn(self.db_file) as conn:
            sql = "SELECT COUNT(*) FROM data WHERE dataset=?"
            c = conn.cursor()
            result = c.execute(sql, (dataset, )).fetchone()[0]
        return result

    def _index(self, prefix="data", types=("id", "idx")):
        """create an index on one db table"""

        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            ci = "CREATE INDEX "
            for x in types:
                index_id = prefix + "_" + x
                cur.execute("DROP INDEX IF EXISTS " + index_id)
                cur.execute(ci + index_id + " on " + prefix + " (dataset, " + x + ")")
            conn.commit()

    def index(self, table_name):
        """create indexes on existing tables in the database"""

        info("Indexing " + table_name + " table")
        if table_name == "data":
            self._index(table_name, types=["id", "idx"])
        elif table_name == "counts":
            self._index(table_name, types=["idx"])

    def get_feature_map(self):
        """construct a feature map"""

        sql = "SELECT id, idx, weight FROM features ORDER by idx"
        result = dict()
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            for row in cur:
                result[row["id"]] = (row["idx"], row["weight"])
        self.n_features = len(result)
        return result

    def set_feature_map(self, feature_map):
        """add content into the feature map table"""

        sql = "INSERT INTO features (id, idx, weight) VALUES (?, ?, ?)"
        data_array = []
        for id, v in feature_map.items():
            data_array.append((id, v[0], v[1]))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
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
        sql = "INSERT INTO counts (dataset, idx, data) VALUES (?, ?, ?)"
        data_array = []
        for i in range(len(data)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((dataset, i, idata))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    @valid_dataset
    def update_counts(self, dataset, data):
        """change existing rows of counts

        :param dataset: string or int, identifier for a dataset
        :param data: dict mapping indexes to csr_matrices
        """

        self.counts_cache.clear()
        sql = "UPDATE counts SET data=? where dataset=? AND idx=?"
        data_array = []
        for i, v in data.items():
            idata = sqlite3.Binary(csr_to_bytes(v))
            data_array.append((idata, dataset, i))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

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

        sql = "INSERT INTO data" +\
              " (dataset, id, idx, title, data) VALUES (?, ?, ?, ?, ?)"
        data_array = []
        for i in range(len(ids)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((dataset, ids[i], indexes[i], titles[i], idata))
        with get_conn(self.db_file) as conn:
            conn.cursor().executemany(sql, data_array)
            conn.commit()
        return indexes

    @valid_dataset
    def get_counts(self, dataset, idxs):
        """retrieve information from counts tables.

        Uses cache when available. Fetches remaining items from db.

        :param dataset: string or int, dataset identifier
        :param idxs: list of integers
        :return: dictionary mapping indexes to count csr_matrix objects
        """

        n_features = self.n_features
        result, missing = self.counts_cache.get(dataset, idxs)
        if len(missing) == 0:
            return result

        sql = "SELECT idx, data FROM counts WHERE dataset=? "
        sql_where = ["idx=?"]*len(missing)
        sql += "AND (" + " OR ".join(sql_where) + ")"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [dataset]
            vals.extend(missing)
            c.execute(sql, vals)
            for row in c:
                row_counts = bytes_to_csr(row["data"], n_features)
                result[row["idx"]] = row_counts
                self.counts_cache.set(dataset, row["idx"], row_counts)
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
        sql = "SELECT data FROM " + table + " WHERE dataset=?"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            c.execute(sql, (dataset,))
            for row in c:
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

        # perform query
        sql = "SELECT id, idx, data FROM data WHERE dataset=? AND "
        sql_where = [column + "=?"]*len(missing)
        sql += "(" + " OR ".join(sql_where) + ")"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [dataset]
            vals.extend(missing)
            c.execute(sql, vals)
            for row in c:
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
        sql = "SELECT id, idx, data FROM data WHERE dataset=? ORDER BY idx"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            c.execute(sql, (dataset,))
            for row in c:
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
        result, missing = self.titles_cache.get(dataset, queries)
        if len(missing) == 0:
            return result

        sql = "SELECT id, idx, title FROM data WHERE dataset=? AND "
        sql_where = [column + "=?"]*len(missing)
        sql += "(" + " OR ".join(sql_where) + ")"
        result = dict()
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [dataset]
            vals.extend(missing)
            c.execute(sql, vals)
            for row in c:
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
        sql = "SELECT id, idx FROM data WHERE dataset=? AND "
        sql += "(" + " OR ".join(["idx=?"]*len(idxs)) + " )"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [dataset]
            vals.extend(idxs)
            c.execute(sql, vals)
            result = {row["idx"]: row["id"] for row in c}
        return result

    @valid_dataset
    def has_id(self, dataset, id):
        """check if database has an item with specified string identifier

        (Used before manual insertion of a new item, to avoid nonunique ids)

        :param dataset: string, dataset identifier
        :param id: string identifier to query
        :return: boolean
        """

        sql = "SELECT id, idx FROM data WHERE dataset=? AND id=?"
        with get_conn(self.db_file) as conn:
            c = conn.cursor().execute(sql, (dataset, id))
            result = {row["idx"]: row["id"] for row in c}
        return len(result) > 0

    @valid_dataset
    def all_ids(self, dataset):
        """get all ids associated with a dataset

        :param dataset: string or int, indicating to query targets or documents
        :return: list with ids corresponding to those indexes
        """

        count_sql = "SELECT COUNT(*) FROM data WHERE dataset=?"
        select_sql = "SELECT id, idx FROM data WHERE dataset=?"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            n_rows = c.execute(count_sql, (dataset,)).fetchone()[0]
            result = [None]*n_rows
            c.execute(select_sql, (dataset,))
            for row in c:
                result[row["idx"]] = row["id"]
        return result

