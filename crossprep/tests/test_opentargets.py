"""
Tests for building crossmap datasets from opentargets json-like data
"""


import io
import unittest
import yaml
from os.path import join
from crossprep.opentargets.build import build_opentargets_dataset


data_dir = join("crossprep", "tests", "testdata")
# opentargets calls their files "json" but actually they
# are a one-line-per-item format.
# each line is a valid json object, but the lines are all independent
associations_file = join(data_dir, "opentargets.json")


class BuildOpentargetsDatasetTests(unittest.TestCase):
    """creating a dataset from json-like opentargets data."""

    @classmethod
    def setUp(cls):
        # build gene-based dataset
        out_gene = io.StringIO()
        build_opentargets_dataset(associations_file, "MONDO",
                                  "gene", out_gene)
        gene_str = out_gene.getvalue()
        out_gene.close()
        cls.gene_data = yaml.load(gene_str, Loader=yaml.CBaseLoader)
        # build disease-based dataset
        out_disease = io.StringIO()
        build_opentargets_dataset(associations_file, "MONDO",
                                  "disease", out_disease)
        disease_str = out_disease.getvalue()
        out_disease.close()
        cls.disease_data = yaml.load(disease_str, Loader=yaml.CBaseLoader)

    def test_length(self):
        """dataset has two disease ids"""

        # the whole file has three lines, two MONDO ids and one EFO id
        self.assertEqual(len(self.disease_data), 2)
        # the whole file describes only one gene
        self.assertEqual(len(self.gene_data), 1)

    def test_data_components(self):
        """all items should have a data field with components"""
        for k, v in self.disease_data.items():
            self.assertTrue("tractability" in v["data"])
            self.assertTrue("gene" in v["data"])
            self.assertTrue("disease" in v["data"])

    def test_gene(self):
        """item has gene information"""

        self.assertTrue("PIK3CA" in str(self.disease_data))
        self.assertTrue("PIK3CA" in str(self.gene_data))

    def test_disease(self):
        """item has disease information"""

        self.assertTrue("neoplastic" in str(self.disease_data))
        self.assertTrue("neoplastic" in str(self.gene_data))

    def test_tractability(self):
        """item has tractability information"""

        self.assertFalse("antibody" in str(self.disease_data))
        self.assertTrue("molecule" in str(self.disease_data))

