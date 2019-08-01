'''Tests for handling the crossmap data db
'''

import unittest
from scipy.sparse import csr_matrix
from os.path import join, exists
from crossmap.db import CrossmapDB
from crossmap.settings import CrossmapSettings
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
test_feature_map = dict(w=(0,1),
                        x=(1,1),
                        y=(2,1),
                        z=(3,0.5))


class CrossmapDBTests(unittest.TestCase):
    """Creating a DB for holding"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        self.settings = CrossmapSettings(config_plain, create_dir=True)
        self.db_file = self.settings.db_file()

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_build(self):
        """build empty database"""

        self.assertFalse(exists(self.db_file))
        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO") as cm:
            db.build()
        self.assertTrue(exists(self.db_file))
        # all tables should be empty
        self.assertEqual(db._count_rows("features"), 0)
        self.assertEqual(db._count_rows("targets"), 0)
        self.assertEqual(db._count_rows("documents"), 0)
        self.assertEqual(db._count_rows("other_table"), 0)
        # data grab should be empty
        self.assertListEqual(db._get_data(idxs=[0], table="targets"), [])
        self.assertListEqual(db._get_data(idxs=[0], table="documents"), [])

    def test_db_build_and_rebuild(self):
        """build indexes from a simple configuration"""

        db = CrossmapDB(self.db_file)
        # first pass can create a db with an info message
        with self.assertLogs(level="INFO") as cm:
            db.build()
        self.assertTrue("Creating" in str(cm.output))
        # second build can remove existing file and create a new db
        with self.assertLogs(level="WARNING") as cm2:
            db.build(reset=True)
        self.assertTrue("Removing" in str(cm2.output))

    def test_db_feature_map(self):
        """build indexes from a simple configuration"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO") as cm:
            db.build()
        # store a feature map
        self.assertEqual(db.n_features, None)
        db.set_feature_map(test_feature_map)
        self.assertEqual(db.n_features, len(test_feature_map))
        # retrieve a feature map
        result = db.get_feature_map()
        self.assertEqual(len(result), len(test_feature_map))
        for k,v in result.items():
            self.assertListEqual(list(v), list(test_feature_map[k]))

    def test_db_add_get(self):
        """build indexes from a simple configuration"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO") as cm:
            db.build()
            db.set_feature_map(test_feature_map)
        # add data and retrieve data back
        ids = ["a", "b"]
        idxs = [0, 1]
        vec_a = [0.0, 0.0, 1.0, 0.0]
        vec_b = [0.0, 2.0, 0.0, 0.0]
        data = [csr_matrix(vec_a), csr_matrix(vec_b)]
        db.add_documents(data, ids, idxs)
        # retrieve object 'a'
        A = db.get_documents(idxs=[0])
        self.assertEqual(len(A), 1)
        self.assertEqual(A[0]["id"], "a")
        Avec = A[0]["data"].toarray()[0]
        self.assertListEqual(list(Avec), list(vec_a))
        # retrieve object 'b'
        B = db.get_documents(ids=["b"])
        self.assertEqual(len(B), 1)
        self.assertEqual(B[0]["id"], "b")
        Bvec = B[0]["data"].toarray()[0]
        self.assertListEqual(list(Bvec), vec_b)


class CrossmapDBQueriesTests(unittest.TestCase):
    """Querying DB """

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        settings = CrossmapSettings(config_plain, create_dir=True)
        cls.db_file = settings.db_file()
        cls.db = CrossmapDB(cls.db_file)
        with cls.assertLogs(cls, level="INFO"):
            cls.db.build()
        # insert some data
        target_ids = [_ + "_target" for _ in ["a", "b"]]
        doc_ids = [_ + "_doc" for _ in ["a", "b"]]
        data = [csr_matrix([0.0, 1.0]),
                csr_matrix([1.0, 0.0])]
        cls.db.add_targets(data, target_ids, [0,1])
        cls.db.add_documents(data, doc_ids, [0,1])

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_raises_unknown_table(self):
        # raise errors when query strange table
        with self.assertRaises(Exception):
            self.db.ids([0,1], table="abc")

    def test_ids_from_named_table(self):
        """standard retrieval, user specifying table by string name"""
        # raise errors when query strange table
        self.assertListEqual(self.db.ids([0,1], table="targets"),
                             ["a_target", "b_target"])
        self.assertListEqual(self.db.ids([0,1], table="documents"),
                             ["a_doc", "b_doc"])

    def test_ids_from_int_table(self):
        """standard retrieveal, user specifying table by 0/1"""
        self.assertListEqual(self.db.ids([0,1], table=0),
                             ["a_target", "b_target"])
        self.assertListEqual(self.db.ids([0,1], table=1),
                             ["a_doc", "b_doc"])

    def test_ids_empty_queries(self):
        """retrieval, input is emptyy"""
        self.assertListEqual(self.db.ids([], table=0), [])

    def test_ids_singles(self):
        self.assertListEqual(self.db.ids([0], table=0), ["a_target"])

    def test_ids_error_out_of_bounds(self):
        """when provided indexes are out-of-range, ids will give error"""
        with self.assertRaises(KeyError):
            self.db.ids([0,5], table=0)
        with self.assertRaises(KeyError):
            self.db.ids([6,5], table=0)
