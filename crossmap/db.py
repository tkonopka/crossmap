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
    result = ([float(_) for _ in x.data],
              [int(_) for _ in x.indices],
              [int(_) for _ in x.indptr])
    return dumps(result)


def bytes_to_csr(x, n_features):
    """convert a bytes object into a csr row matrix

    :param x: bytes object
    :param n_features: integer, number of features (columns) in csr matrix
    :return:
    """
    return csr_matrix(loads(x), shape=(1, n_features))


class CrossmapDB:
    """Management of a DB for features and data vectors"""

    def __init__(self, db_file):
        """sets up path to db, operations performed via functions"""

        self.db_file = db_file
        self.n_features = None

    def _count_rows(self, table="features"):
        """generic function to count rows in any table within db

        :param table: string, table name
        :return: integer number of rows
        """

        if table not in ["features", "targets", "documents"]:
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
        """create"""

        if exists(self.db_file):
            if not reset:
                return
            warning("Removing existing database")
            remove(self.db_file)

        info("Creating database")
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            CT = "CREATE TABLE "
            sql_map = CT + "features (id TEXT, idx INTEGER, weight REAL)"
            sql_targets = CT + "targets (id TEXT, idx INTEGER, data BLOB)"
            sql_docs = CT + "documents (id TEXT, idx INTEGER, data BLOB)"
            cur.execute(sql_map)
            cur.execute(sql_targets)
            cur.execute(sql_docs)
            conn.commit()

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

    def _add_data(self, data, ids, indexes=None, tab="targets"):
        """insert data items into db

        Arguments:
            data      list with vectors
            ids       list with string-like identifiers
            indexes   list with integers identifiers
            tab       string, one of 'targets' or 'documents'
        """
        if indexes is None:
            indexes = list(range(len(ids)))

        sql = "INSERT INTO " + tab + " (id, idx, data) VALUES (?, ?, ?);"
        data_array = []
        for i in range(len(ids)):
            idata = csr_to_bytes(data[i])
            data_array.append((ids[i], indexes[i], sqlite3.Binary(idata)))
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.executemany(sql, data_array)
            conn.commit()

    def add_targets(self, data, ids, indexes):
        """record items in the db as targets"""
        self._add_data(data, ids, indexes, tab="targets")

    def add_documents(self, data, ids, indexes):
        """record items in the db as documents"""
        self._add_data(data, ids, indexes, tab="documents")

    def _get_data(self, idxs=None, ids=None, table="targets"):
        """retrieve information from db from targets or documents

        Note: one of ids or idx must be specified other than None

        :param ids: list of string ids to query in column "id"
        :param idxs: list of integer indexes to query in column "idx"
        :param table: one of 'targets' or 'documents'
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
        sql = "SELECT id, idx, data FROM " + table + " WHERE "
        sql_where = [column + "=?"]*len(queries)
        sql += " OR ".join(sql_where)
        result = []
        with get_conn(self.db_file) as conn:
            cur = conn.cursor()
            cur.execute(sql, queries)
            for row in cur:
                rowdict = dict(id=row["id"], idx=row["idx"],
                               data=bytes_to_csr(row["data"], n_features))
                result.append(rowdict)
        return result

    def get_targets(self, idxs=None, ids=None):
        """get information on target items

        :param idxs: list of integer indexes, or None to use ids instead
        :param ids: list of text ids, or None to use idxs instead
        :return: array of dicts
        """
        return self._get_data(idxs=idxs, ids=ids, table="targets")

    def get_documents(self, idxs=None, ids=None):
        """get information on documents

        :param idxs: list of integer indexes, or None to use ids instead
        :param ids: list of text ids, or None to use idxs instead
        :return: array of dicts
        """
        return self._get_data(idxs=idxs, ids=ids, table="documents")
