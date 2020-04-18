"""
Tests for querying an instance for distances, diffusion, etc.
"""

import yaml
import unittest
from os.path import join
from crossmap.settings import CrossmapSettings
from crossmap.crossmap import Crossmap
from crossmap.info import CrossmapInfo
from .tools import remove_crossmap_cache

data_dir = join("tests", "testdata")
config_plain = join(data_dir, "config-simple.yaml")
dataset_file = join(data_dir, "dataset.yaml")


class CrossmapInfoTests(unittest.TestCase):
    """initialization of an info object"""

    @classmethod
    def setUpClass(cls):
        cls.settings = CrossmapSettings(config_plain)
        cls.crossmap = Crossmap(cls.settings)
        cls.crossmap.build()
        cls.crossinfo = CrossmapInfo(cls.settings)

    @classmethod
    def tearDownClass(cls):
        remove_crossmap_cache(data_dir, "crossmap_simple")

    def test_info_has_feature_maps(self):
        """info object exists and initialized feature maps"""

        info = self.crossinfo
        self.assertEqual(len(info.feature_map), len(info.inv_feature_map))
        # inverse map should be a simple list with feature strings
        self.assertTrue("a" in info.inv_feature_map)

    def test_info_formats_features(self):
        """info formats feature map for JSON-like output"""

        features = self.crossinfo.features()
        self.assertEqual(len(self.crossinfo.feature_map), len(features))
        # features should be an array of dictionaries
        self.assertTrue(type(features[0]) is dict)
        self.assertTrue("feature" in features[0])
        self.assertTrue("weight" in features[0])

    def test_info_summary(self):
        """info summarizes counts and sparsite of all datasets"""

        summary = self.crossinfo.summary(3)
        # summary should have some keys
        self.assertTrue("name" in summary and "dir" in summary)
        self.assertTrue("datasets" in summary)
        # summary data should reflect the instance
        self.assertEqual(summary["features"], len(self.crossinfo.feature_map))
        # there are 2 datasets (targets, document)
        self.assertEqual(len(summary["datasets"]), 2)
        datasets = set([_["label"] for _ in summary["datasets"]])
        self.assertEqual(datasets, set(["targets", "documents"]))

    def test_info_vectors(self):
        """info provides raw data vectors for data items"""

        # objects in the targets dataset
        vectors_targets = self.crossinfo.vectors(ids=["A", "B"])
        self.assertEqual(len(vectors_targets), 2)
        self.assertEqual(vectors_targets[0]["dataset"], "targets")
        self.assertEqual(vectors_targets[1]["dataset"], "targets")
        # objects in the documents dataset
        vectors_docs = self.crossinfo.vectors(ids=["U:E"])
        self.assertEqual(len(vectors_docs), 1)
        self.assertEqual(vectors_docs[0]["dataset"], "documents")
        # document U:E has four tokens
        num_nonzero = sum([_ > 0 for _ in vectors_docs[0]["vector"]])
        self.assertEqual(num_nonzero, 4)

    @unittest.skip
    def test_info_vectors_diffusion(self):
        """info can return diffused vectors"""

        result = self.crossinfo.vectors(ids=["U:E"],
                                        diffusion={"targets": 1})
        vector = result[0]["vector"]
        self.assertGreater(sum([_>0 for _ in vector]), 4)

    def test_info_vectors_from_file(self):
        """info can make vectors from file data items"""

        diff = {"targets": 0.0}
        # vectors can scan data files
        from_file = self.crossinfo.vectors(dataset_file, diffusion=diff)
        self.assertGreater(len(from_file), 3)
        self.assertEqual(from_file[0]["dataset"], "_file_")
        # vectors from file should match vectors from db
        c_file = None
        for d in from_file:
            if d["id"] == "C":
                c_file = d["vector"]
        from_db = self.crossinfo.vectors(ids=["C"], diffusion=diff)
        c_db = from_db[0]["vector"]
        for i in range(len(c_db)):
            self.assertAlmostEqual(c_file[i], c_db[i])

    def test_info_distances_from_file(self):
        """compute distances between data items in a file and in db"""

        result = self.crossinfo.distance_file(dataset_file, ids=["A", "B"])
        # self-distance is zero
        aa = [_ for _ in result if _["query"] == "A" and _["id"] == "A"]
        self.assertEqual(len(aa), 1)
        self.assertEqual(aa[0]["distance"], 0)
        # distance to other objects is greater than zero
        cb = [_ for _ in result if _["query"] == "C" and _["id"] == "B"]
        self.assertEqual(len(cb), 1)
        self.assertGreater(cb[0]["distance"], 0)
        # result does not include hits to other ids no specified in ids=...
        e = [_ for _ in result if _["id"] == "E"]
        self.assertEqual(len(e), 0)

    def test_info_distances_match_search_wo_diffusion(self):
        """info can reproduce distances reported via search"""

        doc = {"data": "alpha A", "aux_pos": "bravo B"}
        # distances from search
        search_result = self.crossmap.search(doc, "targets", n=4)
        search_targets = search_result["targets"]
        search_distances = dict()
        for i, d in enumerate(search_result["distances"]):
            search_distances[search_targets[i]] = d
        # distances computed through info
        result = self.crossinfo.distance(doc, ids=search_targets)
        info_distances = dict()
        for _ in result:
            info_distances[_["id"]] = _["distance"]
        self.assertEqual(len(search_distances), len(info_distances))
        for id in search_targets:
            self.assertAlmostEqual(search_distances[id], info_distances[id],
                                   places=5)

    def test_info_distances_match_search_w_diffusion(self):
        """info can reproduce distances reported via search"""

        doc = {"data": "alpha A", "aux_pos": "bravo"}
        # distances from search
        diff = dict(targets=1)
        crossmap = self.crossmap
        search_result = crossmap.search(doc, "targets", n=4, diffusion=diff)
        search_targets = search_result["targets"]
        search_distances = dict()
        for i, d in enumerate(search_result["distances"]):
            search_distances[search_targets[i]] = d
        # distances computed through info
        result = self.crossinfo.distance(doc, ids=search_targets, diffusion=diff)
        info_distances = dict()
        for _ in result:
            info_distances[_["id"]] = _["distance"]
        self.assertEqual(len(search_distances), len(info_distances))
        for id in search_targets:
            self.assertAlmostEqual(search_distances[id], info_distances[id],
                                   places=5)

    def test_info_matrix_details(self):
        """compute details for distances"""

        result = self.crossinfo.matrix(ids=["A", "B"])
        self.assertGreater(len(result), 2)
        self.assertTrue("A" in result[0])
        self.assertTrue("B" in result[0])

