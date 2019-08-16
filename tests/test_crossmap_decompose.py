'''Tests for decomposing documents into basis vectors
'''

import unittest
from os.path import join
from crossmap.crossmap import Crossmap
from crossmap.tools import yaml_document
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file= join(data_dir, "config-similars.yaml")
dataset_file = join(data_dir, "dataset-similars.yaml")


class CrossmapDecomposeTests(unittest.TestCase):
    """Decomposing objects onto targets - single documents"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")
        with cls.assertLogs(cls, level="WARNING"):
            cls.crossmap = Crossmap(config_file)
            cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        #print(str(cls.crossmap.settings))
        #print(str(cls.crossmap.settings.features))
        #print(str(cls.crossmap.indexer.feature_map))
        #print("")

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")

    def test_decompose_BD(self):
        """object matching against B and D"""

        doc = dict(data="Bob Bravo Delta David", aux_pos="Bob Bernard")
        # standard nearest neighbors should return two Bs
        prediction = self.crossmap.predict(doc, n_targets=2)
        self.assertTrue("B1" in prediction["targets"])
        self.assertTrue("B2" in prediction["targets"])
        self.assertEqual(len(prediction["targets"]), 2)
        # decomposition should give one B and one D
        decomposition = self.crossmap.decompose(doc, n_targets=2)
        self.assertTrue(decomposition["targets"][0] in set(["B1", "B2"]))
        self.assertTrue(decomposition["targets"][1] in set(["D1", "D2"]))

    def test_decompose_CC(self):
        """object matching against Cs"""

        doc = dict(data="Charlie Christine Camilla", aux_pos="Bob Charlie Charlie")
        # standard nearest neighbors should return two Cs
        prediction = self.crossmap.predict(doc, n_targets=2)
        self.assertTrue("C1" in prediction["targets"])
        self.assertTrue("C2" in prediction["targets"])
        self.assertEqual(len(prediction["targets"]), 2)
        # decomposition should also give Cs
        decomposition = self.crossmap.decompose(doc, n_targets=2)
        self.assertTrue(decomposition["targets"][0] in set(["C1", "C2"]))
        self.assertTrue(decomposition["targets"][1] in set(["C1", "C2"]))

    def test_decompose_empty_doc(self):
        """decomposing an empty document should not raise exceptions"""

        doc = dict(data="", aux_pos="")
        decomposition = self.crossmap.decompose(doc, n_targets=3)
        self.assertEqual(decomposition["targets"], [])
        self.assertEqual(decomposition["coefficients"], [])


class CrossmapDecomposeBatchTests(unittest.TestCase):
    """Decomposing objects onto targets - in batch"""

    @classmethod
    def setUpClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")
        with cls.assertLogs(cls, level="WARNING"):
            cls.crossmap = Crossmap(config_file)
            cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        cls.targets = dict()
        targets_file = cls.crossmap.settings.files("targets")[0]
        with open(targets_file, "rt") as f:
            for id, doc in yaml_document(f):
                cls.targets[id] = doc

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")

    def test_decompose_documents(self):
        """exact document matches should produce short decomposition vectors"""

        targets_file = self.crossmap.settings.files("targets")[0]
        result = self.crossmap.decompose_file(targets_file, 2)
        for i in range(len(result)):
            iresult = result[i]
            # all targets should match to themselves only, with coeff 1.0
            self.assertTrue(iresult["targets"][0] in self.targets)
            self.assertEqual(len(iresult["targets"]), 1)
            self.assertEqual(len(iresult["coefficients"]), 1)
            self.assertEqual(iresult["coefficients"][0], 1.0)