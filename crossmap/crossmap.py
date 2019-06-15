"""Crossmap class

@author: Tomasz Konopka
"""

import logging
import functools
from umap import UMAP
from sklearn.utils import check_random_state
from collections import Counter
from os.path import join, exists, basename
from .tokens import Kmerizer
from .data import CrossmapData
from .tools import read_csv_set, write_csv
from .tools import read_dict, write_dict
from .tools import read_obj, write_obj, write_matrix
from .settings import CrossmapSettings
from .neighbors import neighbors


def require_valid(function):
    """Decorator, check if class is .valid before computation."""

    @functools.wraps(function)
    def wrapped(self, *args, **kw):
        if self.valid():
            return function(self, *args, **kw)
        return None

    return wrapped


class Crossmap():

    def __init__(self, config):
        """configure a crossmap object.

        Arguments:
            config  path to a directory containing crossmap.yaml or a
                    yaml configuration file
        """

        settings = CrossmapSettings(config)
        self.settings = settings
        if not settings.valid:
            return
        self.tokenizer = Kmerizer(k=settings.tokens.k,
                                  alphabet=settings.tokens.alphabet,
                                  aux_weight=settings.aux_weight)
        self.random_state = check_random_state(0)

    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid

    @require_valid
    def build(self):
        """build data objects for a crossmap analysis.

        This involves processing tokens in targets and documents and
        creating an embedding.
        """

        s = self.settings
        logging.info("Building: " + s.name)
        project_files = s.files(["targets", "documents"])
        target_ids, target_features = self.targets_features()
        features = self.document_features(target_features, s.max_features)
        self.feature_map = self._feature_map(features)
        self.data_builder = CrossmapData(self.feature_map, self.tokenizer)
        self.data, self.ids  = self._matrix(project_files)
        item_indexes = [-1]*len(self.ids)
        for k,v in self.ids.items():
            item_indexes[v] = k
        self.item_indexes = item_indexes
        self._map = self.umap()
        logging.info("done")

    def _tsv_file(self, label):
        """create a file path for project tsv data"""

        s = self.settings
        return join(s.data_dir, s.name + "-" + label + ".tsv")

    def _pickle_file(self, label):
        """create a file path for project binary data object"""
        s = self.settings
        return join(s.data_dir, s.name + "-" + label)

    def targets_features(self):
        """scan target documents to gather information.

        Returns
            set of target ids
            dict mapping each tokens to numbers of targets containing the token
        """

        tok_file = self._tsv_file("target-features")
        ids_file = self._tsv_file("target-ids")
        if exists(tok_file) and exists(ids_file):
            logging.info("Reading target information (cache)")
            counts = read_dict(tok_file, id_col="id",
                               value_col="count",
                               value_fun=int)
            return read_csv_set(ids_file, "id"), counts

        counts = Counter()
        ids = set()
        for target_file in self.settings.files("targets"):
            logging.info("Extracting features from target file: " +
                         basename(target_file))
            docs = self.tokenizer.tokenize(target_file)
            for k, v in docs.items():
                ids.add(k)
                counts.update(list(v.keys()))
        write_csv(counts, tok_file)
        write_csv(ids, ids_file)
        return ids, dict(counts)

    def _document_features(self, features):
        """count features in document files

        Return:
            Counter mapping tokens to a weight that captures
            the number of documents containing the token, weighted by the
            length of the document.
        """

        result = Counter()
        for doc_file in self.settings.files("documents"):
            logging.info("Extracting features from document file: " +
                         basename(doc_file))
            docs = self.tokenizer.tokenize(doc_file)
            for k, v in docs.items():
                weight = len(features.intersection(v.keys())) / len(v)
                temp = dict()
                for token, value in v.items():
                    temp[token] = value*weight
                result.update(temp)
        return result

    def document_features(self, features, count):
        """extract tokens from documents that co-occur with target features

        Arguments:
            features    set of features that documents should overlap
            count       total number of required features

        Returns:
            set of at least count elements
        """

        features = set(features)
        if len(features) > count:
            logging.info("Skipping feature augmentation")
            return features

        # save feature counts into a disk file
        features_file = self._tsv_file("document-features")
        if not exists(features_file):
            doc_features = self._document_features(features)
            write_dict(doc_features, features_file, value_col="weight")
        else:
            logging.info("Reading document features (cache)")

        # create a set of count features, using all input features and then
        # selecting the most commonly used features in documents
        doc_features = Counter(
            read_dict(features_file, value_col="weight", value_fun=float))
        result = features.copy()
        for k, v in doc_features.most_common():
            if len(result) >= count:
                break
            result.add(k)

        return result

    def _feature_map(self, token_set):
        """create a map between tokens and integers/indexes"""

        feature_file = self._tsv_file("feature-map")
        if not exists(feature_file):
            result = {v: index for index, v in enumerate(token_set)}
            write_dict(result, feature_file, value_col="index")
        return read_dict(feature_file, value_col="index")

    def _matrix(self, paths):
        """build a sparse matrix with features

        Arguments:
            paths   iterable with file paths containing documents

        Returns:
            csr_matrix with data and mapping from document names to indices
        """

        data_file = self._pickle_file("data")
        ids_file = self._pickle_file("ids")
        if not exists(data_file) or not exists(ids_file):
            logging.info("Building feature matrix")
            data, ids = self.data_builder.documents(paths)
            write_obj(data, data_file)
            write_obj(ids, ids_file)
        else:
            logging.info("Fetching feature matrix")
        return read_obj(data_file), read_obj(ids_file)

    def datum(self, doc_name, feature_name):
        """extract one value from the data matrix.
        (This is mainly for debugging)
        """

        feature_name = self.tokenizer.parse(feature_name)[0]
        doc_index = self.ids[doc_name]
        feature_index = self.feature_map[feature_name]
        return self.data[doc_index, feature_index]

    def umap(self):
        """run umap on the project data"""

        umap_file = self._pickle_file("umap")
        embedding_file = self._tsv_file("embedding")
        if not exists(umap_file):
            logging.info("Creating a UMAP embedding "+str(self.data.shape))
            settings = self.settings.umap
            u = UMAP(metric=settings.metric,
                     n_neighbors=min(settings.n_neighbors, len(self.ids)-1),
                     n_components=settings.n_components)
            u.fit(self.data)
            write_obj(u, umap_file)
            write_matrix(u.embedding_, self.ids, embedding_file)
        else:
            logging.info("Loading a cached UMAP embedding")

        return read_obj(umap_file)

    @require_valid
    def predict(self, data_file):
        """map new data objects onto targets"""

        data, ids = self.data_builder.documents([data_file])
        result = dict()
        for k,v in ids.items():
            n_index = neighbors(data[v], self.data, 1)[0]
            result[k] = self.item_indexes[n_index]

        return result
