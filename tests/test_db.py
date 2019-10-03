"""
Tests for handling the crossmap data db
"""

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


class CrossmapDBBuildEmptyTests(unittest.TestCase):
    """Creating an empty DB with basic structure"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        db_file = settings.db_file()
        cls.assertFalse(cls, exists(db_file))
        with cls.assertLogs(cls, level="INFO"):
            db = CrossmapDB(db_file)
            db.build()
            db.register_dataset("targets")
            db.register_dataset("documents")
        cls.assertTrue(cls, exists(db_file))
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_empty_tables(self):
        """all tables should initialy be empty database"""

        # all tables should be empty
        self.assertEqual(self.db._count_rows("features"), 0)
        self.assertEqual(self.db._count_rows("data"), 0)
        self.assertEqual(self.db._count_rows("other_table"), 0)

    def test_db_registered_datasets(self):
        """init script registers two datasets"""

        self.assertEqual(self.db._count_rows("datasets"), 2)

    def test_db_get_data(self):
        """extraction of data from empty db gives empty"""

        self.assertListEqual(self.db.get_data("targets", idxs=[0]), [])
        self.assertListEqual(self.db.get_data("documents", idxs=[0]), [])

    def test_db_get_data_from_nonexistent_table(self):
        """cannot extract data associated with a nonexistent label"""

        with self.assertRaises(Exception):
            db.get_data(idxs=[0], label="abc")


class CrossmapDBBuildAndPopulateTests(unittest.TestCase):
    """Creating a DB, reseting, filling features"""

    def setUp(self):
        self.settings = CrossmapSettings(config_plain, create_dir=True)
        self.db_file = self.settings.db_file()

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_build_and_rebuild(self):
        """build a db from a simple configuration"""

        db = CrossmapDB(self.db_file)
        # first pass can create a db with an info message
        with self.assertLogs(level="INFO") as cm1:
            db.build()
        self.assertTrue("Creating" in str(cm1.output))
        # second build can remove existing file and create a new db
        with self.assertLogs(level="WARNING") as cm2:
            db.build(reset=True)
        self.assertTrue("Removing" in str(cm2.output))

    def test_db_feature_map(self):
        """build process produces a feature map in db"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO"):
            db.build()
        # store a feature map
        self.assertEqual(db.n_features, None)
        db.set_feature_map(test_feature_map)
        self.assertEqual(db.n_features, len(test_feature_map))
        # retrieve a feature map
        result = db.get_feature_map()
        self.assertEqual(len(result), len(test_feature_map))
        for k, v in result.items():
            self.assertListEqual(list(v), list(test_feature_map[k]))


class CrossmapDBMaintenanceTests(unittest.TestCase):
    """Maintenance of db tables"""

    def setUp(self):
        self.settings = CrossmapSettings(config_plain, create_dir=True)
        self.db_file = self.settings.db_file()

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_clear_features(self):
        """can remove contents from a db table"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO"):
            db.build()
        db.set_feature_map(test_feature_map)
        n_features = len(test_feature_map)
        self.assertEqual(db.n_features, n_features)
        self.assertEqual(db._count_rows("features"), n_features)
        db._clear_table("features")
        self.assertEqual(db.n_features, 0)
        self.assertEqual(db._count_rows("features"), 0)

    def test_db_clear_safety(self):
        """clear table implements some safety mechanism"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO"):
            db.build()
        with self.assertRaises(Exception):
            db._clear_table("abc")


class CrossmapDBAddGetTests(unittest.TestCase):
    """Add/Get data from a db"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        db = CrossmapDB(settings.db_file())
        with cls.assertLogs(cls, level="INFO"):
            db.build()
            db.register_dataset("targets")
            db.register_dataset("documents")
            db.set_feature_map(test_feature_map)
        # add data to documents
        ids = ["a", "b"]
        idxs = [0, 1]
        cls.vec_a = [0.0, 0.0, 1.0, 0.0]
        cls.vec_b = [0.0, 2.0, 0.0, 0.0]
        data = [csr_matrix(cls.vec_a), csr_matrix(cls.vec_b)]
        db.add_data("documents", data, ids, indexes=idxs,
                    titles=["A title", "B title"])
        # add data to targets
        ids = ["x"]
        idxs = [0]
        cls.vec_x = [0.0, 0.0, 0.0, 0.5]
        data = [csr_matrix(cls.vec_x)]
        db.add_data("targets", data, ids, indexes=idxs, titles=["X title"])
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_count_data_rows(self):
        """build and count rows in data table for each dataset"""

        documents_size = self.db.dataset_size("documents")
        targets_size = self.db.dataset_size("targets")
        abc_size = self.db.dataset_size("abc")
        self.assertEqual(documents_size, 2)
        self.assertEqual(targets_size, 1)
        self.assertEqual(abc_size, 0)

    def test_get_data_a(self):
        """can retrieve data vectors"""
        A = self.db.get_data("documents", idxs=[0])
        self.assertEqual(len(A), 1)
        self.assertEqual(A[0]["id"], "a")
        Avec = A[0]["data"].toarray()[0]
        self.assertListEqual(list(Avec), list(self.vec_a))

    def test_get_data_b(self):
        """can retrieve data vectors"""
        B = self.db.get_data("documents", ids=["b"])
        self.assertEqual(len(B), 1)
        self.assertEqual(B[0]["id"], "b")
        Bvec = B[0]["data"].toarray()[0]
        self.assertListEqual(list(Bvec), self.vec_b)

    def test_get_titles_by_idx(self):
        """can retrieve titles"""
        A = self.db.get_titles("documents", idxs=[0])
        self.assertEqual(len(A), 1)
        self.assertEqual(A[0], "A title")

    def test_get_titles_by_id(self):
        """can retrieve titles"""
        AB = self.db.get_titles("documents", ids=["a", "b"])
        self.assertEqual(len(AB), 2)
        self.assertEqual(AB["a"], "A title")
        self.assertEqual(AB["b"], "B title")

    def test_get_ids(self):
        """retrieve ids associated with specific datasets"""
        target_ids = self.db.all_ids("targets")
        documents_ids = self.db.all_ids("documents")
        self.assertEqual(len(target_ids), 1)
        self.assertEqual(len(documents_ids), 2)


class CrossmapDBQueriesTests(unittest.TestCase):
    """Querying DB """

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        cls.db_file = settings.db_file()
        cls.db = CrossmapDB(cls.db_file)
        with cls.assertLogs(cls, level="INFO"):
            cls.db.build()
            cls.db.register_dataset("targets")
            cls.db.register_dataset("documents")
        # insert some data
        target_ids = [_ + "_target" for _ in ["a", "b"]]
        doc_ids = [_ + "_doc" for _ in ["a", "b"]]
        data = [csr_matrix([0.0, 1.0]),
                csr_matrix([1.0, 0.0])]
        cls.db.add_data("targets", data, target_ids, indexes=[0,1])
        cls.db.add_data("documents", data, doc_ids, indexes=[0,1])

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_raises_unknown_table(self):
        # raise errors when query strange table
        with self.assertRaises(Exception):
            self.db.ids("abc", [0,1])

    def test_ids_from_named_table(self):
        """standard retrieval, user specifying table by string name"""
        # raise errors when query strange table
        self.assertListEqual(self.db.ids("targets", [0,1]),
                             ["a_target", "b_target"])
        self.assertListEqual(self.db.ids("documents", [0,1]),
                             ["a_doc", "b_doc"])

    def test_ids_empty_queries(self):
        """retrieval, input is emptyy"""
        self.assertListEqual(self.db.ids("targets", []), [])

    def test_ids_singles(self):
        self.assertListEqual(self.db.ids("targets", [0]), ["a_target"])

    def test_ids_error_out_of_bounds(self):
        """when provided indexes are out-of-range, ids will give error"""
        with self.assertRaises(KeyError):
            self.db.ids("targets", [0,5])
        with self.assertRaises(KeyError):
            self.db.ids("targets", [6,5])

