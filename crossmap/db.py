"""Interface to a specialized db (implemented as sqlite)
"""

import sqlite3
from pickle import loads, dumps
from logging import info, warning
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


def bytes_to_csr(x, n_features):
    """convert a bytes object into a csr row matrix

    :param x: bytes object
    :param n_features: integer, number of features (columns) in csr matrix
    :return:
    """
    return csr_matrix(loads(x), shape=(1, n_features))


# categorization of column names by field type
_text_cols = set(["id", "title", "label"])
_int_cols = set(["idx", "dataset"])
_real_cols = set(["weight"])
_blob_cols = set(["data", "counts"])


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


class CrossmapDB:
    """Management of a DB for features and data vectors"""

    table_names = {"features", "datasets", "data", "counts"}

    def __init__(self, db_file):
        """sets up path to db, operations performed via functions"""

        self.db_file = db_file
        self.n_features = None
        self.datasets = dict()

    def _clear_table(self, table="targets"):
        """remove all content from a table

        :param table: string, name of table
        :return: nothing
        """

        if table not in self.table_names:
            raise Exception("clearing not supported for: " + table)
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute("DELETE FROM "+table)
            conn.commit()
        if table == "features":
            self.n_features = 0

    def _count_rows(self, table):
        """generic function to count rows in any table within db

        :param table: string, table name
        :return: integer number of rows
        """

        if table not in self.table_names:
            print("returning zero by fiat")
            return 0
        with get_conn(self.db_file) as conn:
            count_sql = "SELECT COUNT(*) FROM " + table
            result = conn.cursor().execute(count_sql).fetchone()[0]
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

        cols_features = columns_sql(("id", "idx", "weight"))
        cols_datasets = columns_sql(("dataset", "label", "title"))
        cols_data = columns_sql(("dataset", "id", "idx", "title", "data"))
        cols_counts = columns_sql(("dataset", "idx", "counts"))

        info("Creating database")
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute("CREATE TABLE features " + cols_features)
            cur.execute("CREATE TABLE datasets " + cols_datasets)
            cur.execute("CREATE TABLE data" + cols_data)
            cur.execute("CREATE TABLE counts" + cols_counts)
            conn.commit()

    def register_dataset(self, label, title=""):
        """register a dataset label

        :param label: string, a new data set label
        :param title: string, an additional descriptor for the dataset
        :return:
        """

        # identify existing labels
        sql = "SELECT dataset, label FROM datasets ORDER by dataset"
        existing = set()
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            for row in cur:
                existing.add(row["label"])

        if label in existing:
            error("dataset label already exists")
            return

        s = "INSERT INTO datasets (dataset, label, title) VALUES (?, ?, ?);"
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(s, [(len(existing), label, title)])
            self.datasets[label] = len(existing)
            conn.commit()

    def _index(self, prefix="data", types=("id", "idx")):
        """create an index on one db table"""

        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            ci = "CREATE INDEX "
            for x in types:
                index_id = prefix + "_" + x
                cur.execute("DROP INDEX IF EXISTS " + index_id)
                cur.execute(ci + index_id + " on " + prefix + " (" + x + ")")
            conn.commit()

    def index(self):
        """create indexes on existing tables in the database"""
        info("Indexing database")
        self._index()

    def get_feature_map(self):
        """construct a feature map"""

        sql = "SELECT id, idx, weight FROM features ORDER by idx"
        result = dict()
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(sql)
            for row in cur:
                result[row["id"]] = (row["idx"], row["weight"])
        return result

    def set_feature_map(self, feature_map):
        """add content into the feature map table"""

        sql = "INSERT INTO features (id, idx, weight) VALUES (?, ?, ?);"
        data_array = []
        for id, v in feature_map.items():
            data_array.append((id, v[0], v[1]))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
        self.n_features = len(feature_map)

    def _set_counts(self, data, tab="targets"):
        """insert a counts table into db

        Arguments:
            data      list with vectors
            tab       string, one of 'targets' or 'documents'
        """

        sql = "INSERT INTO counts_" + tab + " (idx, counts) VALUES (?, ?);"
        data_array = []
        for i in range(len(data)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((i, idata))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    def add_data(self, label, data, ids, titles=None, indexes=None):
        """

        :param label: string, dataset identifier
        :param data: list with vectors
        :param ids: list with string-like identifiers
        :param titles: list with string-like descriptions
        :param indexes: list with integer identifiers
        :return:
        """

        if indexes is None:
            indexes = list(range(len(ids)))
        if titles is None:
            titles = [""]*len(ids)
        if label not in self.datasets:
            raise Exception("invalid dataset label: " + label)
        d_index = self.datasets[label]

        sql = "INSERT INTO data" +\
              " (dataset, id, idx, title, data) VALUES (?, ?, ?, ?, ?);"
        data_array = []
        for i in range(len(ids)):
            idata = sqlite3.Binary(csr_to_bytes(data[i]))
            data_array.append((d_index, ids[i], indexes[i], titles[i], idata))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    def _get_counts(self, idxs, table="targets"):
        """retrieve information from counts tables

        :param idxs: list of integers
        :param table: one of 'target' or 'documents'
        :return: dictionary mapping indexes to count objects
        """

        n_features = self.n_features
        sql = "SELECT idx, counts FROM counts_" + table + " WHERE "
        sql_where = ["idx=?"]*len(idxs)
        sql += " OR ".join(sql_where)
        result = dict()
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(sql, idxs)
            for row in cur:
                row_counts = bytes_to_csr(row["counts"], n_features)
                result[row["idx"]] = row_counts
        return result

    def get_data(self, label, idxs=None, ids=None):
        """retrieve information from db from targets or documents

        Note: one of ids or idx must be specified other than None

        :param label: string, an identifier for a table
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: list with content of database table
        """

        if label not in self.datasets:
            raise("incorrect dataset label: "+label)

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
            cur = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(queries)
            cur.execute(sql, vals)
            for row in cur:
                rowdict = dict(id=row["id"], idx=row["idx"],
                               data=bytes_to_csr(row["data"], n_features))
                result.append(rowdict)
        return result

    def get_titles(self, label, idxs=None, ids=None):
        """retrieve information from db from targets or documents

        :param label: string identifier for a dataset
        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :return: dictionary mapping ids to titles
        """

        if label not in self.datasets:
            raise Exception("invalid dataset label: " + label)

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
            cur = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(queries)
            cur.execute(sql, vals)
            for row in cur:
                result[row[column]] = row["title"]
        return result

    def ids(self, label, idxs):
        """convert integer indexes to string ids

        :param label: string, identifier for a table
        :param idxs: iterable with numeric indexes. This function only supports
            small vectors of indexes.
        :return: list with ids corresponding to those indexes
        """

        if label not in self.datasets:
            raise Exception("invalid dataset label: " + label)

        if len(idxs) == 0:
            return []
        sql = "SELECT id, idx FROM data WHERE dataset=? AND "
        sql += "(" + " OR ".join(["idx=?"]*len(idxs)) + " )"
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            vals = [self.datasets[label]]
            vals.extend(idxs)
            cur.execute(sql, vals)
            map = {row["idx"]: row["id"] for row in cur}
        # arrange into a list
        result = [None]*len(idxs)
        for i,v in enumerate(idxs):
            result[i] = map[v]
        return result

    def all_ids(self, table="targets"):
        """get all ids

        :param table: string, indicating to query targets or documents
        :return: list with ids corresponding to those indexes
        """

        table = std_table(table)
        n_rows = self._count_rows(table)
        result = [None]*n_rows
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, idx FROM " + table)
            for row in cur:
                result[row["idx"]] = row["id"]
        return result
