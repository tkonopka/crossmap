"""
Tests for turning datasets into tokens
"""

import unittest
import numpy as np
import yaml
from os.path import join, exists
from crossmap.tools import read_obj, write_obj, write_matrix
from crossmap.tools import write_csv, read_csv_set, read_set
from crossmap.tools import write_dict, read_dict
from crossmap.tools import yaml_document
from .tools import remove_cachefile


data_dir = join("tests", "testdata")
tsv_file = join(data_dir, "crossmap-testing-temp.tsv")
good_yaml_file = join(data_dir, "dataset.yaml")
bad_yaml_file = join(data_dir, "bad_data.yaml")


class WriteCsvTests(unittest.TestCase):
    """Writing and reading data from csv files"""

    def tearDown(self):
        remove_cachefile(data_dir, "crossmap-testing-temp.tsv")

    def test_write_dict(self):
        """read back data as a set"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_csv(expected, tsv_file, id_column="id")
        result = read_csv_set(tsv_file, "id")
        self.assertEqual(result, set(expected.keys()))

    def test_read_csv_dict_none(self):
        """reading from None gives empty set"""

        result = read_csv_set(None, "id")
        self.assertEqual(result, set())


class WriteDictTests(unittest.TestCase):
    """Handling feature maps with files"""

    def tearDown(self):
        remove_cachefile(data_dir, "crossmap-testing-temp.tsv")

    def test_read_write_integer_features(self):
        """Configure a crossmap with just a directory"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_dict(expected, tsv_file)
        result = read_dict(tsv_file, value_fun=int)
        self.assertEqual(result, expected)


class ReadSetTests(unittest.TestCase):
    """Read/write set to disk"""

    def tearDown(self):
        remove_cachefile(data_dir, "crossmap-testing-temp.tsv")

    def test_read_write_set(self):
        """save and retrieve a set of items"""

        data = [str(_) for _ in [0, 1, 2, 3, 5, 7]]
        expected = set(data)
        with open(tsv_file, "wt") as f:
            f.write("\n".join(data))
            f.write("\n")
            f.write("\n".join(data))
        result = read_set(tsv_file)
        self.assertEqual(result, expected)

    def test_read_none(self):
        """retrieving from non-existent file gives an empty set"""
        self.assertEqual(read_set(None), set())


class ObjTests(unittest.TestCase):
    """Handling pickling """

    def tearDown(self):
        remove_cachefile(data_dir, "crossmap-testing-temp.tsv")

    def test_read_write_features(self):
        """Configure a crossmap with just a directory"""

        expected = dict(A=0, B=1, Z=3, G=4)
        write_obj(expected, tsv_file)
        result = read_obj(tsv_file)
        self.assertEqual(result, expected)


class WriteMatrixTests(unittest.TestCase):
    """Writing embedding into text files"""

    def tearDown(self):
        remove_cachefile(data_dir, "crossmap-testing-temp.tsv")

    def test_2d_write(self):
        """write a simple 2-coordinates embedding"""

        data = np.array(range(6), dtype=float)
        data.shape = (3,2)
        data[1,1] = 4.4444444444444
        ids = dict(A=0, G=1, Z=2)

        write_matrix(data, ids, tsv_file)
        self.assertTrue(exists(tsv_file))
        with open(tsv_file, "rt") as f:
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

        write_matrix(data, ids, tsv_file, digits=3)
        self.assertTrue(exists(tsv_file))
        with open(tsv_file, "rt") as f:
            result = f.readlines()
        self.assertEqual(result[0], "id\tX1\tX2\tX3\n")
        self.assertEqual(result[1], "X\t0.0\t1.0\t2.0\n")
        self.assertEqual(result[2], "Y\t3.0\t0.123\t5.0\n")


class ReadYamlTests(unittest.TestCase):
    """Read yaml documents one item at a time"""

    def test_signal_incorrect_yaml(self):
        """raise an exception when yaml is incorrect"""

        with self.assertRaises(Exception) as e:
            with open(bad_yaml_file, "r") as f:
                for id, doc in yaml_document(f):
                    pass

    def test_read_yaml(self):
        """read yaml document one item at a time"""

        # read all at once
        with open(good_yaml_file, "r") as f:
            docs = yaml.load(f, yaml.CBaseLoader)
        # read one at a time
        result = dict()
        with open(good_yaml_file, "r") as f:
            for id, doc in yaml_document(f):
                result[id] = doc
        self.assertEqual(len(docs), len(result))
        self.assertSetEqual(set(docs.keys()), set(result.keys()))

