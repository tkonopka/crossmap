'''Tests for turning datasets into tokens

@author: Tomasz Konopka
'''

import unittest
import numpy as np
from os.path import join, exists
from crossmap.tools import read_obj, write_obj, write_matrix
from crossmap.tools import write_csv, read_csv_set
from crossmap.tools import write_dict, read_dict
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
feature_file = join(data_dir, "crossmap0-feature-map.tsv")
embedding_file = join(data_dir, "crossmap0-embedding.tsv")


class WriteCsvTests(unittest.TestCase):
    """Writing and reading data from csv files"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_write_dict(self):
        """Configure a crossmap with just a directory"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_csv(expected, feature_file, id_column="id")
        result = read_csv_set(feature_file, "id")
        self.assertEqual(result, set(expected.keys()))


class WriteDictTests(unittest.TestCase):
    """Handling feature maps with files"""

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_read_write_integer_features(self):
        """Configure a crossmap with just a directory"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_dict(expected, feature_file)
        result = read_dict(feature_file, value_fun=int)
        self.assertEqual(result, expected)


class ObjTests(unittest.TestCase):
    """Handling pickling """

    def setUp(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_read_write_features(self):
        """Configure a crossmap with just a directory"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_obj(expected, feature_file)
        result = read_obj(feature_file)
        self.assertEqual(result, expected)


class WriteMatrixTests(unittest.TestCase):
    """Writing embedding into text files"""

    def tearDown(self):
        remove_crossmap_cache(data_dir, "crossmap0")

    def test_2d_write(self):
        """write a simple 2-coordinates embedding"""

        data = np.array(range(6), dtype=float)
        data.shape = (3,2)
        data[1,1] = 4.4444444444444
        ids = dict(A=0, G=1, Z=2)

        write_matrix(data, ids, embedding_file)
        self.assertTrue(exists(embedding_file))
        with open(embedding_file, "rt") as f:
            result = f.readlines()
        self.assertEqual(result[0], "id\tX1\tX2\n")
        self.assertEqual(result[1], "A\t0.0\t1.0\n")
        self.assertEqual(result[2], "G\t2.0\t4.44444\n")

    def test_3d_write(self):
        """write an embedding with more dimensions"""

        data = np.array(range(6), dtype=float)
        data.shape = (2,3)
        data[1,1] = 0.123123
        ids = dict(X=0, Y=1)

        write_matrix(data, ids, embedding_file, digits=3)
        self.assertTrue(exists(embedding_file))
        with open(embedding_file, "rt") as f:
            result = f.readlines()
        self.assertEqual(result[0], "id\tX1\tX2\tX3\n")
        self.assertEqual(result[1], "X\t0.0\t1.0\t2.0\n")
        self.assertEqual(result[2], "Y\t3.0\t0.123\t5.0\n")

