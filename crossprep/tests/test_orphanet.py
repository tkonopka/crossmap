"""
Tests for building crossmap datasets from orphanet xml
"""


import unittest
from os.path import join
from crossprep.orphanet.build import build_orphanet_dataset


data_dir = join("crossprep", "tests", "testdata")
phenotypes_file = join(data_dir, "orphanet_HPO.xml")
genes_file = join(data_dir, "orphanet_genes.xml")
nomenclature_file = join(data_dir, "orphanet_nomenclature.xml")


class BuildOrphanetDatasetTests(unittest.TestCase):
    """creating a dataset from xml."""

    @classmethod
    def setUp(cls):
        cls.dataset = build_orphanet_dataset(phenotypes_file,
                                             genes_file,
                                             nomenclature_file)

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
        title_1 = result["ORPHA:1"]["data"]["title"]
        title_2 = result["ORPHA:2"]["data"]["title"]
        self.assertTrue("Disorder name 1" in title_1)
        self.assertTrue("Disorder name 2" in title_2)

    def test_disorder_titles(self):
        """disorder names give item titles"""

        result = self.dataset
        # these are titles for the database records
        self.assertEqual("Disorder name 1", result["ORPHA:1"]["title"])
        self.assertEqual("Disorder name 2", result["ORPHA:2"]["title"])

    def test_disorder_phenotypes(self):
        """dataset has two disorders with phenotypes"""

        result = self.dataset
        phen_1 = str(result["ORPHA:1"]["data"]["phenotypes"])
        phen_2 = str(result["ORPHA:2"]["data"]["phenotypes"])
        # data field should have phenotype names and codes, but not HP ids
        # first disease
        self.assertTrue("Macrocephaly" in phen_1)
        self.assertTrue("flattening" in phen_1)
        self.assertTrue("Hyper" in phen_1)
        self.assertFalse("HP:0000316" in phen_1)
        # second disease
        self.assertTrue("palate" in phen_2)
        self.assertTrue("Hydro" in phen_2)
        self.assertTrue("Macrocephaly" in phen_2)
        self.assertFalse("HP:0000238" in phen_2)

    def test_disorder_metadata(self):
        """dataset has two disorders, each with three phenotypes"""

        result = self.dataset
        meta_1 = result["ORPHA:1"]["metadata"]
        meta_2 = result["ORPHA:2"]["metadata"]
        # metadata should have numeric phenotype codes
        self.assertTrue("HP:0000316" in str(meta_1))
        self.assertTrue("HP:0000238" in str(meta_2))

    def test_disorder_genes(self):
        """dataset has two disorders, each with an associated gene"""

        result = self.dataset
        genes_1 = str(result["ORPHA:1"]["data"]["genes"])
        genes_2 = str(result["ORPHA:2"]["data"]["genes"])
        # genes fields should have gene names and symbols
        self.assertTrue("KIF7" in str(genes_1))
        self.assertTrue("kinesin" in str(genes_1))
        self.assertTrue("AGA" in str(genes_2))
        self.assertTrue("aminidase" in str(genes_2))

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
        data = str(result["ORPHA:3"]["data"])
        meta = str(result["ORPHA:3"]["metadata"])
        self.assertTrue("kinesin" in str(data))
        self.assertTrue("HGNC:30497" in str(meta))
        self.assertTrue("Disorder name" in str(data))

    def test_disorder_descriptions(self):
        """dataset should contain descriptions"""

        result = self.dataset
        data_1 = str(result["ORPHA:1"]["data"])
        data_2 = str(result["ORPHA:2"]["data"])
        self.assertTrue("Description of disorder A" in str(data_1))
        self.assertTrue("Description of disorder B" in str(data_2))