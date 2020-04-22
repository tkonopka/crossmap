"""
Constructing feature sets for a Crossmap analysis
"""

import csv
from collections import Counter
from logging import info
from math import log2
from os.path import basename
from sys import maxsize
from .tokenizer import CrossmapTokenizer
from .dbmongo import CrossmapMongoDB as CrossmapDB
from .tools import read_dict


# column titles for feature map files
id_col = "id"
index_col = "index"
weight_col = "weight"


def read_feature_map(filepath):
    """read a feature map from a tsv file."""
    result = dict()
    with open(filepath, "r") as f:
        r = csv.DictReader(f, delimiter="\t", quotechar="'")
        for line in r:
            index = int(line[index_col])
            weight = float(line[weight_col])
            result[line[id_col]] = (index, weight)
    return result


def write_feature_map(feature_map, settings):
    """write an id-index map into a file."""

    filepath = settings.tsv_file("feature-map")
    with open(filepath, "wt") as f:
        f.write(id_col + "\t" + index_col + "\t"+ weight_col+"\n")
        for k, v in feature_map.items():
            f.write(k + "\t" + str(v[0]) + "\t" + str(v[1]) + "\n")


def _count_tokens(tokenizer, files, progress_interval=10000):
    """count tokens in files on disk

    :param tokenizer: object with function .tokenize()
    :param files: dict mapping labels to file paths
    :param progress_interval: integer, interval for print progress messages
    :return: two objects. a counter with token frequencies.
        An integer with total number of data items
    """

    counts = Counter()
    num_items = 0
    for label, f in files.items():
        info("Extracting features: " + label + " (" + basename(f) + ")")
        for _, doc in tokenizer.tokenize_path(f):
            num_items += 1
            if num_items % progress_interval == 0:
                info("Progress: "+str(num_items))
            tokens = set()
            for component in ("data", "data_pos", "data_neg"):
                if component in doc:
                    tokens.update(doc[component].keys())
            counts.update(tokens)

    return counts, num_items


def _feature_weights(count_map, N, model_weights):
    """convert integer counts into weights (real numbers)

    :param count_map: dict mapping features into integers
    :param N: integer, normalization factor, number of items scanned
    :param model_weights: list of length 2, used to define mapping
        between counts and weights, first element is a constant term
        and second element is coefficient of a logarithmic scaling
    :return: dict with same components as count_map
    """
    w0 = model_weights[0]
    w1 = model_weights[1]
    map = count_map
    return {k: (v[0], w0 - w1*log2(v[1]/(N+1))) for k, v in map.items()}


def feature_map(settings, features=None):
    """construct a dict with features

    :param settings: object of class CrossmapSettings
    :param features: list with custom features
    :return: dictionary mapping tokens to 2-tuples with
        feature index and a weight.
        Features correspond to tokens from target files
        and most common tokens from document files.
    """

    # attempt to use predefined file, or build a feature map from scratch
    map_file = settings.features.map_file
    if features is None and map_file is not None:
        info("reading features from prepared dictionary")
        result = read_dict(map_file, id_col="id",
                           value_col="weight", value_fun=float)
        return feature_dict_map(result)
    # attempt to construct from a dict or list
    if features is not None:
        info("reading features from given list/dictionary")
        return feature_dict_map(features)
    info("Extracting features from data files")
    return _feature_map(settings)


def feature_dict_map(weights):
    """construct a dict with features from a weights dictionary

    :param weights: dictionary mapping features to numeric weights
    :return: dictionary from features to a (index, weight)
    """

    if type(weights) is dict:
        result = {k: (i, weights[k]) for i, k in enumerate(weights)}
    else:
        result = {k: (i, 1) for i, k in enumerate(weights)}
    return result


def _feature_map(settings):
    """construct a dict with features

    :param settings: object of class CrossmapSettings

    :return: dictionary mapping tokens to 2-tuples with
        feature index and a weight.
        Features correspond to tokens from target files
        and most common tokens from document files.
    """

    info("Computing feature map")
    max_features = settings.features.max_number
    min_count = settings.features.min_count
    progress = settings.logging.progress
    if max_features == 0:
        max_features = maxsize
    tokenizer = CrossmapTokenizer(settings)
    # get data files - from primary data and from features
    data_files = settings.data.collections.copy()
    data_files.update(settings.features.data_files)
    # scan the files and count tokens
    counts, n = _count_tokens(tokenizer, data_files, progress)
    result = dict()
    for k, v in counts.most_common():
        if len(result) >= max_features:
            break
        if v < min_count:
            continue
        result[k] = [len(result), v]

    return _feature_weights(result, n, settings.features.weighting)


class CrossmapFeatures:

    def __init__(self, settings, features=None, db=None):
        """initialize indexes and their links with the crossmap db

        :param settings:  CrossmapSettings object
        :param features:  list with feature items (used for testing)
        """

        db = db if db is not None else CrossmapDB(settings)
        self.map = db.get_feature_map()
        if len(self.map) == 0:
            self.map = feature_map(settings, features)
            db.set_feature_map(self.map)
            info("Saving feature map")
            write_feature_map(self.map, settings)

    def inv_feature_map(self):
        """construct an inverse feature map"""

        result = [''] * len(self.map)
        for k, v in self.map.items():
            result[v[0]] = k
        return result
