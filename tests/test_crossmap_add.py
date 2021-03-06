"""
Tests for adding documents into a new dataset
"""

import yaml
import unittest
from os.path import join, exists
from crossmap.crossmap import Crossmap
from crossmap.tools import yaml_document
from .tools import remove_crossmap_cache


data_dir = join("tests", "testdata")
config_file = join(data_dir, "config-simple.yaml")
similars_file = join(data_dir, "dataset-similars.yaml")


class CrossmapAddTests(unittest.TestCase):
    """Adding single documents into a dataset"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        cls.db = cls.crossmap.indexer.db
        cls.manual_file = cls.crossmap.settings.yaml_file("manual")
        # at start, project only has "targets" and "documents" datasets

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_add_to_targets(self):
        """cannot add new data to file-derived datasets"""

        doc = dict(data="Alice and Bob, Alpha and Bravo")
        size_before = self.crossmap.indexer.db.count_rows("targets", "data")
        # attempt to add to dataset
        with self.assertRaises(Exception):
            self.crossmap.add(doc, "targets", id="T0")
        # attempt should do nothing, i.e. outcome None, db unchanged
        size_after = self.crossmap.indexer.db.count_rows("targets", "data")
        self.assertEqual(size_before, size_after)

    def test_add_disk_file(self):
        """adding new object should create a disk file"""

        doc = {"data": "alpha bravo charlie"}
        self.crossmap.add("manual", doc, id="Tdisk")
        self.assertTrue(exists(self.manual_file))
        # content of disk file should contain document
        disk_docs = dict()
        with open(self.manual_file, "rt") as f:
            for id, doc in yaml_document(f):
                disk_docs[id] = doc
        self.assertTrue("Tdisk" in disk_docs)
        self.assertTrue("charlie" in disk_docs["Tdisk"]["data"])

    def test_add_simple_item(self):
        """add new object into data table"""

        doc = {"data": "Alice and Bob, Alpha and Bravo"}
        self.crossmap.add("manual", doc, id="T0")
        # the new record should exist in the database
        db = self.crossmap.indexer.db
        self.assertTrue("manual" in db.datasets)
        self.assertGreater(db.count_rows("manual", "data"), 0)
        # db should contain a data record with features from the doc
        doc_data = db.get_data("manual", ids=["T0"])[0]
        fm = self.crossmap.encoder.feature_map
        alice_idx = fm["alice"][0]
        self.assertEqual(doc_data["data"].shape[1], len(fm))
        self.assertGreater(doc_data["data"][0, alice_idx], 0)
        bravo_idx = fm["bravo"][0]
        self.assertGreater(doc_data["data"][0, bravo_idx], 0)

    def test_add_repeat_id(self):
        """cannot add two elements with same id"""

        doc1 = dict(data="new data item")
        # adding this document should be accepted
        self.crossmap.add("manual", doc1, id="T1")
        size_before = self.db.count_rows("manual", "data")
        with open(self.manual_file, "rt") as f:
            lines_before = len(f.readlines())
        # a second attempt to add a doc with same id should not work
        doc2 = {"data": "Another data item"}
        with self.assertRaises(Exception) as cm:
            self.crossmap.add("manual", doc2, id="T1")
        size_after = self.db.count_rows("manual", "data")
        with open(self.manual_file, "rt") as f:
            lines_after = len(f.readlines())
        # the db as well as the file-on-disk should be unchanged
        self.assertEqual(size_before, size_after)
        self.assertEqual(lines_before, lines_after)

    def test_add_preserved_doc_metadata(self):
        """documents may have metadata, which should be preserved"""

        doc1 = dict(data="new data", metadata=dict(abc="xyz"))
        self.crossmap.add("manual", doc1, id="Tadd")
        with open(self.manual_file, "rt") as f:
            manual_data = "".join(f.readlines())
            result = yaml.load(manual_data, Loader=yaml.CBaseLoader)
        self.assertTrue("Tadd" in result)
        result = result["Tadd"]
        self.assertTrue("metadata" in result)
        self.assertTrue("abc" in result["metadata"])
        self.assertEqual(result["metadata"]["abc"], "xyz")

    def test_add_can_overwrite_metadata(self):
        """if metadata is not a dict, its contents is overwritten"""

        doc1 = dict(data="new data", metadata="xyz")
        self.crossmap.add("manual", doc1, id="Toverwrite")
        with open(self.manual_file, "rt") as f:
            manual_data = "".join(f.readlines())
            result = yaml.load(manual_data, Loader=yaml.CBaseLoader)
        self.assertTrue("Toverwrite" in result)
        result = result["Toverwrite"]
        self.assertTrue("metadata" in result)
        self.assertTrue(type(result["metadata"]) is dict)

    def test_add_preserves_arbitrary_fields(self):
        """if metadata is not a dict, its contents is overwritten"""

        doc1 = dict(data="new data", abc=123)
        self.crossmap.add("manual", doc1, id="Tabc")
        with open(self.manual_file, "rt") as f:
            manual_data = "".join(f.readlines())
            result = yaml.load(manual_data, Loader=yaml.CBaseLoader)
        self.assertTrue("Tabc" in result)
        result = result["Tabc"]
        self.assertTrue("abc" in result)
        self.assertEqual(result["abc"], "123")

    def test_adding_items_changes_diffusion(self):
        """add new object into data table"""

        # first add some element
        doc = {"data": "Alice and Bob, Alpha and Bravo"}
        self.crossmap.add("manual", doc, id="I0")
        # look at how diffusion works in the current state
        v = self.crossmap.encoder.document({"data": "Alice"})
        before = self.crossmap.diffuser.diffuse(v, dict(manual=1))
        self.assertGreater(len(before.data), len(v.data))
        # add a second element
        doc2 = {"data": "Alice and Catherine, Charlie and Delta"}
        self.crossmap.add("manual", doc2, id="I1")
        after = self.crossmap.diffuser.diffuse(v, dict(manual=1))
        self.assertGreater(len(after.data), len(before.data))


class CrossmapAddBatchTests(unittest.TestCase):
    """Add many documents into db at once - in batch"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_add_batch(self):
        """exact document matches should produce short decomposition vectors"""

        crossmap = self.crossmap
        self.assertEqual(len(crossmap.db.datasets), 2)
        self.assertFalse("manual" in crossmap.db.datasets)
        idxs = crossmap.add_file("manual", similars_file)
        # the new data shows up in the database
        self.assertEqual(len(crossmap.db.datasets), 3)
        self.assertEqual(crossmap.db.dataset_size("manual"), len(idxs))
        # the new data is ready to be found
        b2 = {"data": "Bravo Bob Benjamin Bernard"}
        hits = crossmap.search(b2, "manual", n=2)
        self.assertEqual(set(hits["targets"]), set(["B1", "B2"]))
        # the first and second hits might be tied because the new data
        # might look equivalent given the feature_map produced by
        # the original config_simple setup


class CrossmapAddDiffusionTests(unittest.TestCase):
    """Adding documents to affect diffusion and search"""

    @classmethod
    def setUpClass(cls):
        cls.crossmap = Crossmap(config_file)
        cls.crossmap.build()
        cls.db = cls.crossmap.indexer.db
        cls.manual_file = cls.crossmap.settings.yaml_file("manual")
        # at start, project only has "targets" and "documents" datasets

        cls.doc_Alice = dict(data="Alice A")
        cls.doc_A = dict(data="A")
        cls.doc_B = dict(data="B")
        cls.doc_AB = dict(data="A B")

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")
        pass

    def test_plain_associations(self):
        """establish associations before adding any new data entries"""

        # diffused "Alice" should connect to A and B
        crossmap = self.crossmap
        d_Alice = crossmap.search(self.doc_Alice, "targets", n=2,
                                  diffusion=dict(documents=1))
        self.assertFalse("U" in d_Alice["targets"])
        self.assertTrue("A" in d_Alice["targets"])
        self.assertTrue("B" in d_Alice["targets"])

        # "A B" with slight diffusion should connect to "A" and "B"
        d_AB = crossmap.search(self.doc_AB, "targets", n=2,
                               diffusion=dict(documents=1))
        self.assertFalse("U" in d_AB["targets"])
        self.assertListEqual(sorted(d_AB["targets"]), ["A", "B"])

    def test_add_positive(self):
        """adding new documents can create new associations"""

        # some new documents that link Alice to other tokens
        pos_docs = [dict(data="Alice unique"),
                    dict(data="Alice token"),
                    dict(data="Alice has unique token"),
                    dict(data="Alice Catherine")]
        docs_indexes = list(range(len(pos_docs)))
        docs_indexes.reverse()
        crossmap = self.crossmap
        for i in docs_indexes:
            crossmap.add("pos", pos_docs[i], id="P"+str(i), rebuild=(i == 0))

        self.assertEqual(crossmap.db.dataset_size("pos"), len(pos_docs))
        d0_Alice = crossmap.search(self.doc_Alice, "targets", n=2,
                                   diffusion=None)
        d1_Alice = crossmap.search(self.doc_Alice, "targets", n=2,
                                   diffusion=dict(pos=1))
        self.assertTrue("A" in d0_Alice["targets"])
        self.assertTrue("A" in d1_Alice["targets"])
        self.assertTrue("U" in d1_Alice["targets"])

    def test_add_negative(self):
        """adding documents with neg associations can remove links"""

        # some new documents that link Alice to other tokens
        neg_docs = [dict(data_pos="A", data_neg="B"),
                    dict(data_pos="Alice", data_neg="Bob")]
        docs_indexes = list(range(len(neg_docs)))
        docs_indexes.reverse()
        crossmap = self.crossmap
        for i in docs_indexes:
            crossmap.add("neg", neg_docs[i], id="N"+str(i), rebuild=(i==0))
        self.assertEqual(crossmap.db.dataset_size("neg"), 2)

        # entry "A" should link to B before, but not after adding
        d0_A = crossmap.search(self.doc_A, "targets", n=2,
                               diffusion=dict(documents=0.5))
        d1_A = crossmap.search(self.doc_A, "targets", n=2,
                               diffusion=dict(documents=0.5, neg=1))
        self.assertEqual(d0_A["targets"][0], "A")
        self.assertEqual(d1_A["targets"][0], "A")
        self.assertTrue("B" in d0_A["targets"])
        self.assertFalse("B" in d1_A["targets"])

        # entry "B" should link to A before, but not after adding
        d0_B = crossmap.search(self.doc_B, "targets", n=2,
                               diffusion=dict(documents=0.5))
        d1_B = crossmap.search(self.doc_B, "targets", n=2,
                               diffusion=dict(documents=0.5, neg=1))
        self.assertEqual(d0_B["targets"][0], "B")
        self.assertEqual(d1_B["targets"][0], "B")
        self.assertTrue("A" in d0_B["targets"])
        self.assertFalse("A" in d1_B["targets"])

    def test_add_compound_negative(self):
        """adding documents with multiple words and neg associations"""

        # new document has two words in data pos
        neg_doc = dict(data_pos="A Alice", data_neg="B")
        crossmap = self.crossmap
        crossmap.add("compound", neg_doc, id="N0", rebuild=True)
        self.assertEqual(crossmap.db.dataset_size("compound"), 1)

        # diffusion should transfer weight from A to -B but not Alice
        result_a = crossmap.diffuse(dict(data="A"), diffusion={"compound": 1})
        features_a = [_["feature"] for _ in result_a["features"]]
        self.assertEqual(len(features_a), 3)
        self.assertTrue("a" in features_a and "b" in features_a)
        self.assertTrue("alice" in features_a)
        # diffusion should also transfer from B to -A to -Alice
        result_b = crossmap.diffuse(dict(data="B"), diffusion={"compound": 1})
        features_b = [_["feature"] for _ in result_b["features"]]
        self.assertEqual(len(features_b), 3)
        self.assertTrue("alice" in features_b)

    def test_add_diffuse_two_pass(self):
        """adding documents with neg associations can remove links"""

        # some new documents that link Alice to other tokens
        crossmap = self.crossmap
        crossmap.diffuser.num_passes = 1
        a_1 = crossmap.search(self.doc_A, "targets", n=2,
                              diffusion=dict(documents=0.5))
        crossmap.diffuser.num_passes = 2
        a_2 = crossmap.search(self.doc_A, "targets", n=2,
                              diffusion=dict(documents=0.5))
        self.assertEqual(a_1["targets"][0], "A")
        self.assertEqual(a_2["targets"][0], "A")
        self.assertNotEqual(a_1["distances"][0], a_2["distances"][0])
        self.assertNotEqual(a_1["distances"][1], a_2["distances"][1])
