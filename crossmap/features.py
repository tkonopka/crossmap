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


def write_feature_map(feature_map, filepath):
    """write an id-index map into a file."""
    with open(filepath, "wt") as f:
        f.write(id_col + "\t" + index_col + "\t"+ weight_col+"\n")
        for k, v in feature_map.items():
            f.write(k + "\t" + str(v[0]) + "\t" + str(v[1]) + "\n")


def _count_tokens(tokenizer, files):
    """count totkens in files on disk

    :param tokenizer: object with function .tokenize()
    :param files: list with file paths

    :return: two objects.
        a counter with token frequencies
        an integer with total number of data items
    """

    counts = Counter()
    num_items = 0
    ids = set()
    for f in files:
        info("Extracting features from file: " + basename(f))
        docs = tokenizer.tokenize(f)
        num_items += len(docs)
        for k, v in docs.items():
            ids.add(k)
            counts.update(list(v.keys()))

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
    if use_cache and exists(cache_file):
        info("Reading feature map from file: " + basename(cache_file))
        result = read_feature_map(cache_file)
        info("Feature map size: "+str(len(result)))
        return result

    info("Computing feature map")
    max_features = settings.features.max_number
    if max_features == 0:
        max_features = maxsize
    info("Max features is "+str(max_features))
    tokenizer = CrossmapTokenizer(settings)
    target_files = settings.files("targets")
    target_counts, n_targets = _count_tokens(tokenizer, target_files)
    result = dict()
    for k,v in target_counts.items():
        result[k] = [len(result), v]
    doc_counts, n_docs = _count_tokens(tokenizer, settings.files("documents"))
    for k, v in doc_counts.most_common():
        if k in result:
            result[k][1] += v
        if len(result) >= max_features:
            break
        result[k] = [len(result), v]

    if settings.features.weighting == "ic":
        result = _normalize_ic(result, n_targets + n_docs)
    else:
        result = _normalize_constant(result)

    info("Feature map size: "+str(len(result)))
    if use_cache:
        info("Saving feature map")
        write_feature_map(result, cache_file)
    return result

