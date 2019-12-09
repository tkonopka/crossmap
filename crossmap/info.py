"""
Add-on class to use a crossmap object to extract diagnostic information
"""

import logging
from scipy.sparse import csr_matrix
from .distance import sparse_euc_distance
from .vectors import sparse_to_dense
from .tools import open_file, yaml_document
from .crossmap import Crossmap


class CrossmapInfo(Crossmap):

    def __init__(self, settings):
        """start up an existing crossmap project

        :param settings: a CrossmapSettings object
        """

        logging.getLogger().setLevel("ERROR")
        super().__init__(settings)
        self.load()

        # set up a conversion from indexes into feature strings
        self.feature_map = self.indexer.feature_map
        self.inv_feature_map = ['']*len(self.feature_map)
        for k,v in self.feature_map.items():
            self.inv_feature_map[v[0]] = k

    def diffuse(self, doc, diffusion=None):
        """provide an explanation for diffusion in terms of original features

        :param doc: csr_matrix or a dictionary with raw data (will be tokenized before being diffused)
        :param diffusion: dictionary
        :return:
        """

        v = doc
        if type(doc) is not csr_matrix:
            v = self.indexer.encode_document(doc)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)

        result = []
        inv_feature_map = self.inv_feature_map
        for i, d in zip(v.indices, v.data):
            result.append([abs(d), round(d, 6), inv_feature_map[i]])
        result = sorted(result, reverse=True)
        return [{"feature": v[2], "value": v[1]} for i, v in enumerate(result)]

    def diffuse_ids(self, dataset, ids, diffusion=None):
        """compute diffusion for database entries"""

        result = []
        if ids is None or len(ids) == 0:
            return result
        for d in self.db.get_data(dataset, ids=ids):
            for d_result in self.diffuse(d["data"], diffusion):
                d_result["input"] = d["id"]
                result.append(d_result)
        return result

    def diffuse_text(self, items, diffusion=None):
        """compute diffusion for individual features"""

        result = []
        if items is None or len(items) == 0:
            return result
        for d in items:
            for d_result in self.diffuse({"data": d}, diffusion):
                d_result["input"] = d
                result.append(d_result)
        return result

    def diffuse_file(self, paths, diffusion=None):
        """compute diffusion for items from a file"""

        result = []
        if paths is None or len(paths) == 0:
            return result
        for filepath in paths:
            with open_file(filepath, "rt") as f:
                for id, doc in yaml_document(f):
                    for d_result in self.diffuse(doc, diffusion):
                        d_result["input"] = id
                        result.append(d_result)
        return result

    def distance(self, doc, ids=[], diffusion=None, query_name="query"):
        """compute distances from one document to specific items in db

        :param doc: dictionary with text
        :param ids: array of string ids, targets or documents
        :param diffusion: dict, map of diffusion strengths
        :param query_name: string, an identifier to associate with the doc
        :return: list of objects containing id and distance
        """

        result = []
        v = self.indexer.encode_document(doc)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)
        distance = sparse_euc_distance
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    x_vector = x_data[0]["data"]
                    x_dist = distance(v, x_vector)
                    x_result = dict(query=query_name, dataset=label,
                                    id=x, distance=x_dist)
                    result.append(x_result)

        return result

    def distance_file(self, filepath, ids=[], diffusion=None):
        """compute distances from items in a file to specific items in db

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffusion: dict, map of diffusion strengths
        :return: list
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.distance(doc, ids, diffusion, query_name=id))
        return result

    def vectors(self, filepath, ids=[], diffusion=None):
        """extraction of data vectors

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffusion: dict, map of diffusion strengths
        :return: list
        """

        result = []
        # convert db items into vectors
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    v = x_data[0]["data"]
                    if diffusion is not None:
                        v = self.diffuser.diffuse(v, diffusion)
                    v = list(sparse_to_dense(v))
                    x_result = dict(dataset=label, id=x, vector=v)
                    result.append(x_result)

        if filepath is None:
            return result

        # convert from-file items into vectors
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                v = self.indexer.encode_document(doc)
                if diffusion is not None:
                    v = self.diffuser.diffuse(v, diffusion)
                v = list(sparse_to_dense(v))
                result.append(dict(dataset="_file_", id=id, vector=v))
        return result

    def counts(self, label, features=[], digits=6):
        """extract count vectors associated with features

        :param features: list of features
        :return:
        """

        # convert features into indexes, and an inverse mapping
        fm, ifm = self.indexer.feature_map, dict()
        idxs = []
        for f in features:
            if f in fm:
                ifm[fm[f][0]] = f
                idxs.append(fm[f][0])

        counts = self.indexer.db.get_counts(label, idxs)
        result = []
        for k, v in counts.items():
            vlist = list(sparse_to_dense(v))
            vmax = max(vlist)
            vlist = [round(_/vmax, digits) for _ in vlist]
            result.append(dict(feature=ifm[k], counts=vlist))
        return result

    def features(self):
        """extract feature information"""

        result = []
        for k, v in self.indexer.feature_map.items():
            result.append(dict(feature=k, index=v[0], weight=v[1]))
        return result

    def summary(self, digits=4):
        """prepare an ad-hoc summary of the contents of the configuration"""

        def stats(x):
            if len(x) == 0:
                return {"min": 0, "mean": 0, "max": 0}
            temp = dict(min=min(x), mean=sum(x)/len(x), max=max(x))
            return {k: round(v, digits) for k, v in temp.items()}

        db = self.db
        datasets = []
        for dataset in db.datasets:
            size = db.dataset_size(dataset)
            counts_sparsity = stats(db.sparsity(dataset, "counts"))
            data_sparsity = stats(db.sparsity(dataset, "data"))
            datasets.append(dict(label=dataset, size=size,
                                 counts_sparsity=counts_sparsity,
                                 data_sparsity=data_sparsity))

        return dict(name=self.settings.name,
                    dir=self.settings.dir,
                    features=len(self.indexer.feature_map),
                    datasets=datasets)

