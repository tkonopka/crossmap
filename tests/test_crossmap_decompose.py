"""
Tests for decomposing documents into basis vectors
"""

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
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")

    def test_decompose_BD(self):
        """object matching against B and D"""

        doc = dict(data="Bob Bravo Delta David. Bob Bravo Bernard")
        # standard nearest neighbors should return two Bs
        prediction = self.crossmap.search(doc, "targets", n=2)
        self.assertTrue("B1" in prediction["targets"])
        self.assertTrue("B2" in prediction["targets"])
        self.assertEqual(len(prediction["targets"]), 2)
        # decomposition should give one B and one D
        decomposition = self.crossmap.decompose(doc, "targets", n=2)
        BD = set(["B1", "B2", "D1", "D2"])
        self.assertTrue(decomposition["targets"][0] in BD)
        self.assertTrue(decomposition["targets"][1] in BD)

    def test_decompose_CC(self):
        """object matching against Cs"""

        doc = dict(data="Charlie Christine Camilla. Bob Charlie Charlie")
        # standard nearest neighbors should return two Cs
        prediction = self.crossmap.search(doc, "targets", n=2)
        self.assertTrue("C1" in prediction["targets"])
        self.assertTrue("C2" in prediction["targets"])
        self.assertEqual(len(prediction["targets"]), 2)
        # decomposition should also give Cs
        decomposition = self.crossmap.decompose(doc, "targets", n=2)
        self.assertTrue(decomposition["targets"][0] in set(["C1", "C2"]))
        self.assertTrue(decomposition["targets"][1] in set(["C1", "C2"]))

    def test_decompose_empty_doc(self):
        """decomposing an empty document should not raise exceptions"""

        doc = dict(data="", aux_pos="")
        decomposition = self.crossmap.decompose(doc, "targets", n=3)
        self.assertEqual(decomposition["targets"], [])
        self.assertEqual(decomposition["coefficients"], [])


class CrossmapDecomposeBatchTests(unittest.TestCase):
    """Decomposing objects onto targets - in batch"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        cls.feature_map = cls.crossmap.indexer.feature_map
        targets = dict()
        targets_file = cls.crossmap.settings.data_files["targets"]
        with open(targets_file, "rt") as f:
            for id, doc in yaml_document(f):
                targets[id] = doc
        cls.targets = targets

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_similars")

    def test_decompose_documents(self):
        """exact document matches should produce short decomposition vectors"""

        targets_file = self.crossmap.settings.data_files["targets"]
        result = self.crossmap.decompose_file(targets_file, "targets", 2)
        for i in range(len(result)):
            iresult = result[i]
            # all targets should match to themselves only, with coeff 1.0
            self.assertTrue(iresult["targets"][0] in self.targets)
            self.assertEqual(len(iresult["targets"]), 1)
            self.assertEqual(len(iresult["coefficients"]), 1)
            self.assertAlmostEqual(iresult["coefficients"][0], 1.0)

