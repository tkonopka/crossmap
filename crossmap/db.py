"""
Interface to a specialized db (implemented as sqlite)
"""

import sqlite3
from functools import wraps
from pickle import loads, dumps
from logging import info, warning, error
from os.path import exists
from os import remove
from scipy.sparse import csr_matrix


def get_conn(dbfile, timeout=5000):
    """get a connection to a databse"""
    conn = sqlite3.connect(dbfile, timeout=timeout)
    conn.row_factory = sqlite3.Row
    return conn


def csr_to_bytes(x):
    """Convert a csr row vector into a bytes-like object

    :param x: csr matrix
    :return: bytes-like object
    """
    result = (tuple([float(_) for _ in x.data]),
              tuple([int(_) for _ in x.indices]),
              tuple([int(_) for _ in x.indptr]))
    return dumps(result)


def bytes_to_csr(x, ncol):
    """convert a bytes object into a csr row matrix

    :param x: bytes object
    :param ncol: integer, number of columns in csr matrix
    :return: csr_matrix
    """
    return csr_matrix(loads(x), shape=(1, ncol))


# categorization of column names by field type
_text_cols = set(["id", "title", "label"])
_int_cols = set(["idx", "dataset"])
_real_cols = set(["weight"])
_blob_cols = set(["data"])


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
    """decorator to check if a dataset is declared in the db."""

    @wraps(f)
    def wrapped(self, dataset, *args, **kw):
        if dataset not in self.datasets:
            raise Exception("Invalid dataset: "+str(dataset))
        return f(self, dataset, *args, **kw)
    return wrapped


class CrossmapDB:
    """Management of a DB for features and data vectors"""

    def __init__(self, db_file):
        """sets up path to db, operations performed via functions"""

        self.db_file = db_file
        self.n_features = None
        self.datasets = self._datasets()

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

    def _clear_table(self, table="features", dataset=None):
        """remove all content from a table

        :param table: string, name of table
        :param dataset: string, dataset identifier
        """

        if table not in crossmap_table_names:
            raise Exception("clearing not supported for: " + table)
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            sql = "DELETE FROM " + table
            if dataset is not None:
                sql += " WHERE dataset=?"
                c.execute(sql, (self.datasets[dataset],))
            else:
                c.execute(sql)
            conn.commit()
        if table == "features":
            self.n_features = 0

    def _count_rows(self, table, dataset=None):
        """generic function to count rows in any table within db

        :param table: string, table name
        :param dataset: string, dataset identifier
        :return: integer number of rows
        """

        if table not in crossmap_table_names:
            return 0
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            sql = "SELECT COUNT(*) FROM " + table
            if dataset is not None:
                d_index = self.datasets[dataset]
                sql += " WHERE dataset=?"
                c = c.execute(sql, (d_index, ))
            else:
                c = c.execute(sql)
            result = c.fetchone()[0]
        return result

    def count_features(self):
        """count the number of features defined in the features map"""

        self.n_features = self._count_rows("features")
        return self.n_features

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

        :param dataset: string, identifier for a dataset
        :return: integer, number of data rows associated to a dataset
        """

        d_index = self.datasets[dataset]
        with get_conn(self.db_file) as conn:
            sql = "SELECT COUNT(*) FROM data WHERE dataset=?"
            c = conn.cursor()
            result = c.execute(sql, (d_index, )).fetchone()[0]
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
        """insert rows into the counts table

        :param dataset: string, identifier for a dataset
        :param data: list with rows to insert
        """

        d_index = self.datasets[dataset]
        sql = "INSERT INTO counts (dataset, idx, data) VALUES (?, ?, ?)"
        data_array = []
        for i in range(len(data)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((d_index, i, idata))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    @valid_dataset
    def update_counts(self, label, data):
        """change existing rows of counts

        :param label: string, identifier for a dataset
        :param data: dict mapping indexes to csr_matrices
        :return:
        """

        d_index = self.datasets[label]
        sql = "UPDATE counts SET data=? where dataset=? AND idx=?"
        data_array = []
        for i, v in data.items():
            idata = sqlite3.Binary(csr_to_bytes(v))
            data_array.append((d_index, i, idata))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    @valid_dataset
    def add_data(self, label, data, ids, titles=None, indexes=None):
        """insert rows into the 'data' table

        :param label: string, dataset identifier
        :param data: list with vectors
        :param ids: list with string-like identifiers
        :param titles: list with string-like descriptions
        :param indexes: list with integer identifiers
        :return:
        """

        if indexes is None:
            current_size = self.dataset_size(label)
            indexes = [current_size + _ for _ in range(len(ids))]
        if titles is None:
            titles = [""]*len(ids)
        d_index = self.datasets[label]

        sql = "INSERT INTO data" +\
              " (dataset, id, idx, title, data) VALUES (?, ?, ?, ?, ?)"
        data_array = []
        for i in range(len(ids)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((d_index, ids[i], indexes[i], titles[i], idata))
        with get_conn(self.db_file) as conn:
            conn.cursor().executemany(sql, data_array)
            conn.commit()

    @valid_dataset
    def get_counts(self, label, idxs):
        """retrieve information from counts tables

        :param label: string, dataset identifier
        :param idxs: list of integers
        :return: dictionary mapping indexes to count objects
        """

        n_features = self.n_features
        sql = "SELECT idx, data FROM counts WHERE dataset=? "
        sql_where = ["idx=?"]*len(idxs)
        sql += "AND (" + " OR ".join(sql_where) + ")"
        result = dict()
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(idxs)
            c.execute(sql, vals)
            for row in c:
                row_counts = bytes_to_csr(row["data"], n_features)
                result[row["idx"]] = row_counts
        return result

    @valid_dataset
    def sparsity(self, dataset, table="counts"):
        """compute sparsity values for all items in data or counts tables

        :param dataset: string, identifier for a dataset
        :param table: string, one 'counts' or 'data'
        :return: list of sparsity values for all relevant rows in the table
        """

        if table not in set(["data", "counts"]):
            raise Exception("invalid table")

        result = []
        n_features = self.n_features
        sql = "SELECT data FROM " + table + " WHERE dataset=? "
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            c.execute(sql, (self.datasets[dataset],))
            for row in c:
                v = bytes_to_csr(row["data"], n_features)
                result.append(len(v.indices) / n_features)
        return result

    @valid_dataset
    def get_data(self, label, idxs=None, ids=None):
        """retrieve information from db from targets or documents

        Note: one of ids or idx must be specified other than None

        :param label: string, an identifier for a table
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: list with content of database table
        """

        # determine whether to query by test id or numeric indexes
        queries, column = idxs, "idx"
        if ids is not None:
            queries, column = ids, "id"
        if queries is None or len(queries) == 0:
            return []
        # get dimensions of feature vector
        if self.n_features is None:
            self.n_features = self.count_features()
        n_features = self.n_features
        # perform query
        sql = "SELECT id, idx, data FROM data WHERE dataset=? AND "
        sql_where = [column + "=?"]*len(queries)
        sql += "(" + " OR ".join(sql_where) + ")"
        result = []
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(queries)
            c.execute(sql, vals)
            for row in c:
                rowdict = dict(id=row["id"], idx=row["idx"],
                               data=bytes_to_csr(row["data"], n_features))
                result.append(rowdict)
        return result

    @valid_dataset
    def all_data(self, dataset):
        """generator for data rows for a specific dataset

        :param dataset: string, dataset identifier
        :return: dict with data entries
        """

        n_features = self.n_features
        sql = "SELECT id, idx, data FROM data WHERE dataset=? ORDER BY idx"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            c.execute(sql, (self.datasets[dataset],))
            for row in c:
                result = dict(id=row["id"], idx=row["idx"],
                              data=bytes_to_csr(row["data"], n_features))
                yield result

    @valid_dataset
    def get_titles(self, label, idxs=None, ids=None):
        """retrieve information from db from targets or documents

        :param label: string identifier for a dataset
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: dictionary mapping ids to titles
        """

        queries, column = idxs, "idx"
        if ids is not None:
            queries, column = ids, "id"
        if queries is None or len(queries) == 0:
            return dict()
        sql = "SELECT id, idx, title FROM data WHERE dataset=? AND "
        sql_where = [column + "=?"]*len(queries)
        sql += "(" + " OR ".join(sql_where) + ")"
        result = dict()
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(queries)
            c.execute(sql, vals)
            for row in c:
                result[row[column]] = row["title"]
        return result

    @valid_dataset
    def ids(self, label, idxs):
        """convert integer indexes to string ids

        :param label: string, identifier for a table
        :param idxs: iterable with numeric indexes. This function only supports
            small vectors of indexes.
        :return: list with ids corresponding to those indexes
        """

        if len(idxs) == 0:
            return []
        sql = "SELECT id, idx FROM data WHERE dataset=? AND "
        sql += "(" + " OR ".join(["idx=?"]*len(idxs)) + " )"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(idxs)
            c.execute(sql, vals)
            map = {row["idx"]: row["id"] for row in c}
        result = [None]*len(idxs)
        for i,v in enumerate(idxs):
            result[i] = map[v]
        return result

    @valid_dataset
    def has_id(self, dataset, id):
        """check if database has an item with specified string identifier

        :param dataset: string, dataset identifier
        :param id: string identifier to query
        :return: boolean
        """

        sql = "SELECT id, idx FROM data WHERE dataset=? AND id=?"
        with get_conn(self.db_file) as conn:
            c = conn.cursor().execute(sql, (self.datasets[dataset], id))
            result = {row["idx"]: row["id"] for row in c}
        return len(result) > 0

    @valid_dataset
    def all_ids(self, dataset):
        """get all ids associated with a dataset

        :param dataset: string, indicating to query targets or documents
        :return: list with ids corresponding to those indexes
        """

        d_index = self.datasets[dataset]
        count_sql = "SELECT COUNT(*) FROM data WHERE dataset=?"
        select_sql = "SELECT id, idx FROM data WHERE dataset=?"
        with get_conn(self.db_file) as conn:
            c = conn.cursor()
            # first count rows that belong to this dataset
            n_rows = c.execute(count_sql, (d_index,)).fetchone()[0]
            # second query retrieve ids and idx
            result = [None]*n_rows
            c.execute(select_sql, (d_index,))
            for row in c:
                result[row["idx"]] = row["id"]
        return result

