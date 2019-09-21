"""constructing a set of features for a Crossmap analysis
"""

import csv
from collections import Counter
from logging import info
from math import log2
from os.path import exists, basename
from sys import maxsize
from .tokens import CrossmapTokenizer


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


def _count_tokens(tokenizer, files):
    """count tokens in files on disk

    :param tokenizer: object with function .tokenize()
    :param files: list with file paths

    :return: two objects.
        a counter with token frequencies
        an integer with total number of data items
    """

    counts = Counter()
    num_items = 0
    for f in files:
        info("Extracting features from file: " + basename(f))
        for id, doc in tokenizer.tokenize_path(f):
            num_items += 1
            if num_items % 100000 == 0:
                info("Number of items: "+str(num_items))
            tokens = set()
            for component in ("data", "aux_pos", "aux_neg"):
                if component in doc:
                    tokens.update(doc[component].keys())
            counts.update(tokens)

    return counts, num_items


def _normalize_constant(count_map):
    """normalize a feature map giving each feature a unit weight

    :param count_map: dict mapping features to (index, count)
    :return: a dict mapping features to (index, 1)
    """
    return {k: (v[0], 1) for k, v in count_map.items()}


def _normalize_ic(count_map, N):
    """normalize a feature map using information content, -log(p)

    :param count_map: dict mapping features to (index, count)
    :param N: integer, total number of documents
    :return: dict mapping features to (index, weight)
    """
    return {k: (v[0], -log2(v[1]/(N+1))) for k, v in count_map.items()}


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


def feature_map(settings, use_cache=True):
    """construct a dict with features

    :param settings: object of class CrossmapSettings
    :param use_cache: logical, whether to use fetch data from cache

    :return: dictionary mapping tokens to 2-tuples with
        feature index and a weight.
        Features correspond to tokens from target files
        and most common tokens from document files.
    """

    cache_file = settings.tsv_file("feature-map")
    result = None
    if use_cache and exists(cache_file):
        info("Reading feature map from file: " + basename(cache_file))
        result = read_feature_map(cache_file)
        use_cache = False
    if result is None:
        result = _feature_map(settings)
    info("Feature map size: "+str(len(result)))
    if use_cache:
        info("Saving feature map")
        write_feature_map(result, settings)
    return result


def feature_dict_map(settings, weights):
    """construct a dict with features from a weights dictionary"""

    if type(weights) is dict:
        result = {k: (i, weights[k]) for i, k in enumerate(weights)}
    else:
        result = {k: (i, 1) for i, k in enumerate(weights)}
    write_feature_map(result, settings)
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
    if max_features == 0:
        max_features = maxsize
    else:
        info("Max features is "+str(max_features))
    tokenizer = CrossmapTokenizer(settings)
    target_files = settings.files("targets")
    target_counts, n_targets = _count_tokens(tokenizer, target_files)
    result = dict()
    for k, v in target_counts.items():
        result[k] = [len(result), v]
    doc_counts, n_docs = _count_tokens(tokenizer, settings.files("documents"))
    for k, v in doc_counts.most_common():
        if len(result) >= max_features:
            break
        if k in result:
            result[k][1] += v
        else:
            result[k] = [len(result), v]

    N = n_targets + n_docs
    result = _feature_weights(result, N, settings.features.weighting)

    return result

