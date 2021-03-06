"""
Add-on class to use a crossmap object to extract diagnostic information
"""

import logging
from math import sqrt
from scipy.sparse import csr_matrix
from .distance import sparse_euc_distance
from .vectors import sparse_to_dense
from .tools import open_file, yaml_document
from .crossmap import Crossmap


# special constant
sqrt2 = sqrt(2.0)


class CrossmapInfo(Crossmap):

    def __init__(self, settings):
        """start up an existing crossmap project

        :param settings: a CrossmapSettings object
        """

        logging.getLogger().setLevel("ERROR")
        super().__init__(settings)
        self.load()
        # set up a conversion from indexes into feature strings
        encoder = self.indexer.encoder
        self.feature_map = encoder.feature_map
        # inv_feature_map is list of strings.
        # Given an index i, inv_feature_map[i] gives the feature string
        self.inv_feature_map = encoder.inv_feature_map

    def diffuse(self, doc, diffusion=None):
        """provide an explanation for diffusion in terms of original features

        :param doc: csr_matrix or a dictionary with raw data (will be tokenized before being diffused)
        :param diffusion: dictionary
        :return:
        """

        v = doc
        if not isinstance(doc, csr_matrix):
            v = self.indexer.encode_document(doc)
        if diffusion is not None:
            v = self.diffuser.diffuse(v, diffusion)

        result = []
        inv_feature_map = self.inv_feature_map
        for i, d in zip(v.indices, v.data):
            result.append([abs(d), _r(d, 6), inv_feature_map[i]])
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
        v_raw, v_diffused = self._prep_vector(doc, diffusion)
        distance = sparse_euc_distance
        db = self.indexer.db
        for x in ids:
            for label in db.datasets.keys():
                x_data = db.get_data(label, ids=[x])
                if len(x_data) > 0:
                    x_vector = x_data[0]["data"]
                    x_dist = distance(v_diffused, x_vector) / sqrt2
                    x_result = dict(query=query_name,
                                    dataset=label,
                                    id=x,
                                    distance=x_dist)
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
                result.extend(self.distance(doc, ids, diffusion,
                                            query_name=id))
        return result

    def compare_file(self, filepath, ids=[], diffusion=None):
        """compute representations from items in a file to specific items in db

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffusion: dict, map of diffusion strengths
        :return: list
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.extend(self.distance(doc, ids, diffusion,
                                            query_name=id))
        return result

    def vectors(self, filepath=None, ids=[], diffusion=None):
        """extract of data vectors for db items or disk items

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
                    v = list(sparse_to_dense(v))
                    x_result = dict(dataset=label, id=x, vector=v)
                    result.append(x_result)

        if filepath is None:
            return result

        # convert items from file into vectors
        encoder = self.indexer.encoder
        with open_file(filepath, "rt") as f:
            for doc_id, doc in yaml_document(f):
                v = encoder.document(doc)
                if diffusion is not None:
                    v = self.diffuser.diffuse(v, diffusion)
                result.append(dict(dataset="_file_", id=doc_id,
                                   vector=list(sparse_to_dense(v))))
        return result

    def matrix(self, filepath=None, ids=[], diffusion=None):
        """extract data for db items or disk items, output as a matrix

        This is similar to vectors, but result is output in a matrix form

        :param filepath: string, path to a data file
        :param ids: list of string ids
        :param diffusion: dict, map of diffusion strengths
        :return: list
        """

        vectors = self.vectors(filepath, ids, diffusion)

        inv_feature_map = self.inv_feature_map
        result = []
        vec_ids = [_["id"] for _ in vectors]
        num_ids = len(vec_ids)
        for i in range(len(inv_feature_map)):
            i_data = [_["vector"][i] for _ in vectors]
            if sum(i_data) == 0:
                continue
            i_result = dict(_feature=inv_feature_map[i],
                            _max=_r(max(i_data)),
                            _min=_r(min(i_data)))
            for j in range(num_ids):
                i_result[vec_ids[j]] = i_data[j]
            result.append(i_result)
        return result

    def counts(self, label, features=[], digits=6):
        """extract count vectors associated with features

        :param label: dataset name
        :param features: list of features
        :param digits: integer, number of digits for output printing
        :return:
        """

        # convert features into indexes, and an inverse mapping
        fm, ifm = self.feature_map, dict()
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
        for k, v in self.feature_map.items():
            result.append(dict(feature=k, index=v[0], weight=v[1]))
        return result

    def summary(self, digits=6):
        """prepare an ad-hoc summary of the contents of the configuration"""

        def stats(x, collection=""):
            temp = dict(min=min(x), mean=sum(x)/len(x), max=max(x))
            result = {"collection": collection}
            for k,v in temp.items():
                result[k] = round(v, digits)
            return result

        db = self.db
        datasets = []
        for dataset in db.datasets:
            size = db.dataset_size(dataset)
            counts_sparsity = stats(db.sparsity(dataset, "counts"), "counts")
            data_sparsity = stats(db.sparsity(dataset, "data"), "data")
            datasets.append(dict(label=dataset, size=size,
                                 sparsity=[counts_sparsity, data_sparsity])),

        return dict(name=self.settings.name,
                    dir=self.settings.dir,
                    features=len(self.feature_map),
                    datasets=datasets)


def _distance_details(a, b, features):
    """prepare details for the distance between two items

    :param a: csr vector
    :param b: csr vector
    :param features: vector with string representations of features
    :return: array, each element is a dictionary holding feature name
        and a squared-distance value
    """

    a_dense = sparse_to_dense(a)
    b_dense = sparse_to_dense(b)
    result = []
    for i in range(len(a_dense)):
        i_d = a_dense[i]-b_dense[i]
        if abs(i_d) > 0:
            result.append((i_d*i_d, i_d, i))
    result = sorted(result, reverse=True)
    return [{"feature": features[k], "value": _r(v)} for v2, v, k in result]


def _r(x, digits=6):
    """round a number"""
    return round(x, ndigits=digits)

