"""
Tests for building crossmap datasets from orphanet xml
"""


import unittest
from os.path import join
from crossprep.orphanet.build import build_orphanet_dataset


data_dir = join("crossprep", "tests", "testdata")
phenotypes_file = join(data_dir, "orphanet_HPO.xml")
genes_file = join(data_dir, "orphanet_genes.xml")


class BuildOrphanetDatasetTests(unittest.TestCase):
    """creating a dataset from xml."""

    @classmethod
    def setUp(cls):
        cls.dataset = build_orphanet_dataset(phenotypes_file, genes_file)

    def test_disorders_length(self):
        """dataset has three disorders"""

        # two disorder are defined in phenotypes file,
        # one additional one in genes file
        self.assertEqual(len(self.dataset), 3)

    def test_disorder_ids(self):
        """dataset has two disorders labeled 1, 2, 3"""

        result = list(self.dataset.keys())
        # two ORPHA ids from HPO file, one new one from gene file
        self.assertEqual(sorted(result), ["ORPHA:1", "ORPHA:2", "ORPHA:3"])

    def test_disorder_names(self):
        """dataset has two disorders, their names have an integer in name"""

        result = self.dataset
        self.assertTrue("Disorder name 1" in result["ORPHA:1"]["data"])
        self.assertTrue("Disorder name 2" in result["ORPHA:2"]["data"])

    def test_disorder_titles(self):
        """disorder names give item titles"""

        result = self.dataset
        self.assertEqual("Disorder name 1", result["ORPHA:1"]["title"])
        self.assertEqual("Disorder name 2", result["ORPHA:2"]["title"])

    def test_disorder_phenotypes(self):
        """dataset has two disorders, with phenotypes go into aux"""

        result = self.dataset
        aux_1 = str(result["ORPHA:1"]["aux_pos"])
        aux_2 = str(result["ORPHA:2"]["aux_pos"])
        # aux should have phenotype names and codes, but not HP ids
        # first disease
        self.assertTrue("Macrocephaly" in aux_1)
        self.assertTrue("flattening" in aux_1)
        self.assertTrue("Hyper" in aux_1)
        self.assertFalse("HP:0000316" in aux_1)
        # second disease
        self.assertTrue("palate" in aux_2)
        self.assertTrue("Hydro" in aux_2)
        self.assertTrue("Macrocephaly" in aux_2)
        self.assertFalse("HP:0000238" in aux_2)

    def test_disorder_metadata(self):
        """dataset has two disorders, each with three phenotypes"""

        result = self.dataset
        meta_1 = result["ORPHA:1"]["metadata"]
        meta_2 = result["ORPHA:2"]["metadata"]
        # aux should have phenotype names and codes
        self.assertTrue("HP:0000316" in str(meta_1))
        self.assertTrue("HP:0000238" in str(meta_2))

    def test_disorder_genes(self):
        """dataset has two disorders, each with an associated gene"""

        result = self.dataset
        aux_1 = str(result["ORPHA:1"]["aux_pos"])
        aux_2 = str(result["ORPHA:2"]["aux_pos"])
        # aux should have gene names and symbols
        self.assertTrue("KIF7" in str(aux_1))
        self.assertTrue("kinesin" in str(aux_1))
        self.assertTrue("AGA" in str(aux_2))
        self.assertTrue("aminidase" in str(aux_2))

    def test_disorder_external_genes(self):
        """dataset has two disorders, each mapped to HGNC id"""

        result = self.dataset
        meta_1 = str(result["ORPHA:1"]["metadata"])
        meta_2 = str(result["ORPHA:2"]["metadata"])
        self.assertTrue("HGNC:30497" in str(meta_1))
        self.assertTrue("ENSG00000166813" in str(meta_1))
        self.assertTrue("HGNC:318" in str(meta_2))
        self.assertTrue("ENSG00000038002" in str(meta_2))

    def test_disorder_names_from_genes_file(self):
        """gene dataset contains a disorder that is not in HPO file"""

        result = self.dataset
        aux = str(result["ORPHA:3"]["aux_pos"])
        data = str(result["ORPHA:3"]["data"])
        meta = str(result["ORPHA:3"]["metadata"])
        self.assertTrue("kinesin" in str(aux))
        self.assertTrue("HGNC:30497" in str(meta))
        self.assertTrue("Disorder name" in str(data))

