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

    def test_db_build_and_rebuild(self):
        """build indexes from a simple configuration"""

        self.assertFalse(exists(self.db_file))
        db = CrossmapDB(self.db_file)
        # first pass can create a db with an info message
        with self.assertLogs(level="INFO") as cm:
            db.build()
        self.assertTrue("Creating" in str(cm.output))
        self.assertTrue(exists(self.db_file))
        # second build can remove existing file and create a new db
        with self.assertLogs(level="WARNING") as cm2:
            db.build(reset=True)
        self.assertTrue("Removing" in str(cm2.output))

    def test_db_add_get(self):
        """build indexes from a simple configuration"""

        db = CrossmapDB(self.db_file)
        with self.assertLogs(level="INFO") as cm:
            db.build()
        # setting features will set n_features
        self.assertEqual(db.n_features, None)
        db.set_feature_map(test_feature_map)
        self.assertEqual(db.n_features, len(test_feature_map))
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


