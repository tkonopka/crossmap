"""
Tests for handling the crossmap data db (mongodb)
"""

import unittest
from scipy.sparse import csr_matrix
from os.path import join, exists
from crossmap.dbmongo import CrossmapMongoDB
from crossmap.settings import CrossmapSettings
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
test_feature_map = dict(w=(0, 1),
                        x=(1, 1),
                        y=(2, 1),
                        z=(3, 0.5))


class CrossmapMongoDBBuildEmptyTests(unittest.TestCase):
    """Creating an empty DB with basic structure"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        db = CrossmapMongoDB(settings)
        db.register_dataset("targets")
        db.register_dataset("documents")
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_empty_tables(self):
        """all tables should initially be empty database"""

        # all tables should be empty
        self.assertEqual(self.db.count_rows("targets", "data"), 0)
        self.assertEqual(self.db.count_rows("targets", "counts"), 0)

    def test_db_get_data(self):
        """extraction of data from empty db gives empty"""

        self.assertListEqual(self.db.get_data("targets", idxs=[0]), [])
        self.assertListEqual(self.db.get_data("documents", idxs=[0]), [])

    def test_db_get_data_from_nonexistent_table(self):
        """cannot extract data associated with a nonexistent label"""

        with self.assertRaises(Exception):
            self.db.get_data(idxs=[0], dataset="abc")

    def test_valid_labels(self):
        """db can signal that a new dataset label is allowed"""

        self.assertEqual(self.db.validate_dataset_label("abc"), 1)
        self.assertEqual(self.db.validate_dataset_label("a0_8"), 1)
        self.assertEqual(self.db.validate_dataset_label("123"), 1)

    def test_invalid_labels_exist(self):
        """db can signal that a dataset label because it already exists"""

        # two labels already exist
        self.assertEqual(self.db.validate_dataset_label("targets"), 0)
        self.assertEqual(self.db.validate_dataset_label("documents"), 0)

    def test_invalid_labels_bad_form(self):
        """db can signal that a label is bad, incorrect types etc."""

        # certain labels are just not allowed
        self.assertEqual(self.db.validate_dataset_label(4), -1)
        self.assertEqual(self.db.validate_dataset_label("a.b"), -1)
        self.assertEqual(self.db.validate_dataset_label("a b"), -1)

    def test_invalid_labels_special_cases(self):
        """db can signal that a label is invalid, special cases"""

        # labels cannot start or end in underscores
        self.assertEqual(self.db.validate_dataset_label("_leading"), -1)
        self.assertEqual(self.db.validate_dataset_label("trailing_"), -1)


class CrossmapMongoDBBuildAndPopulateTests(unittest.TestCase):
    """Creating a DB, reseting, filling features"""

    def setUp(self):
        self.settings = CrossmapSettings(config_plain, create_dir=True)

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_db_rebuild(self):
        """rebuild a db from a simple configuration"""

        db = CrossmapMongoDB(self.settings)
        with self.assertLogs(level="WARNING") as cm2:
            db.rebuild()
        self.assertTrue("Removing" in str(cm2.output))

    def test_db_feature_map(self):
        """build process produces a feature map in db"""

        db = CrossmapMongoDB(self.settings)
        # store a feature map
        self.assertEqual(db.n_features, 0)
        db.set_feature_map(test_feature_map)
        self.assertEqual(db.n_features, len(test_feature_map))
        # retrieve a feature map
        result = db.get_feature_map()
        self.assertEqual(len(result), len(test_feature_map))
        for k, v in result.items():
            self.assertListEqual(list(v), list(test_feature_map[k]))


class CrossmapMongoDBAddGetTests(unittest.TestCase):
    """Add/Get data from a db"""

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        db = CrossmapMongoDB(settings)
        db.register_dataset("targets")
        db.register_dataset("documents")
        db.set_feature_map(test_feature_map)
        # add data to documents
        ids = ["a", "b"]
        idxs = [0, 1]
        cls.vec_a = [0.0, 0.0, 1.0, 0.0]
        cls.vec_b = [0.0, 2.0, 0.0, 0.0]
        data = [csr_matrix(cls.vec_a), csr_matrix(cls.vec_b)]
        db.add_data("documents", data, ids, idxs=idxs)
        db.add_docs("documents", [dict(title="A title"), dict(title="B title")],
                    ids, idxs)
        # add data to targets
        ids = ["x"]
        idxs = [0]
        cls.vec_x = [0.0, 0.0, 0.0, 0.5]
        data = [csr_matrix(cls.vec_x)]
        db.add_data("targets", data, ids, idxs=idxs)
        db.add_docs("targets", [dict(title="X title")], ids, idxs)
        cls.db = db

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_count_data_rows(self):
        """count rows in data table for each dataset"""

        documents_size = self.db.dataset_size("documents")
        targets_size = self.db.dataset_size("targets")
        self.assertEqual(documents_size, 2)
        self.assertEqual(targets_size, 1)

    def test_dataset_integer_identifiers(self):
        """count rows for each dataset, using integers as identifiers"""

        documents_id = self.db.datasets["documents"]
        documents_size = self.db.dataset_size(documents_id)
        self.assertEqual(documents_size, 2)

    def test_dataset_unusual_identifiers(self):
        """cannot use strange identifiers to refer to datasets"""

        # a float is an unacceptable identifier
        with self.assertRaises(Exception):
            self.db.dataset_size(1.2)

    def test_count_rows_checks_dataset(self):
        """count_rows checks dataset label is valid"""

        with self.assertRaises(Exception):
            self.db.dataset_size("abc")

    def test_query_contains_identifiers(self):
        """can query yes/no if a dataset contains identifiers"""

        self.assertTrue(self.db.has_id("documents", "a"))
        self.assertTrue(self.db.has_id("documents", "b"))
        self.assertFalse(self.db.has_id("documents", "z"))
        self.assertFalse(self.db.has_id("targets", "a"))

    def test_get_data_a(self):
        """retrieve data vectors"""

        A = self.db.get_data("documents", idxs=[0])
        self.assertEqual(len(A), 1)
        self.assertEqual(A[0]["id"], "a")
        Avec = A[0]["data"].toarray()[0]
        self.assertListEqual(list(Avec), list(self.vec_a))

    def test_get_data_b(self):
        """retrieve data vectors, another example"""

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


class CrossmapMongoDBQueriesTests(unittest.TestCase):
    """Querying DB """

    @classmethod
    def setUpClass(cls):
        settings = CrossmapSettings(config_plain, create_dir=True)
        cls.db = CrossmapMongoDB(settings)
        cls.db.register_dataset("targets")
        cls.db.register_dataset("documents")
        # insert some data
        target_ids = [_ + "_target" for _ in ["a", "b"]]
        doc_ids = [_ + "_doc" for _ in ["a", "b"]]
        data = [csr_matrix([0.0, 1.0]),
                csr_matrix([1.0, 0.0])]
        cls.db.add_data("targets", data, target_ids, idxs=[0, 1])
        cls.db.add_data("documents", data, doc_ids, idxs=[0, 1])

    @classmethod
    def tearDownClass(self):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_raises_unknown_table(self):
        # raise errors when query strange table
        with self.assertRaises(Exception):
            self.db.ids("abc", [0, 1])

    def test_ids_from_named_table(self):
        """standard retrieval, user specifying table by string name"""
        # raise errors when query strange table
        self.assertDictEqual(self.db.ids("targets", [0,1]),
                             {0: "a_target", 1: "b_target"})
        self.assertDictEqual(self.db.ids("documents", [0,1]),
                             {0: "a_doc", 1: "b_doc"})

    def test_ids_empty_queries(self):
        """retrieval, input is empty"""

        self.assertDictEqual(self.db.ids("targets", []), dict())

    def test_ids_singles(self):
        """retrieval of a single id gives a dict with one element"""

        self.assertDictEqual(self.db.ids("targets", [0]), {0: "a_target"})

