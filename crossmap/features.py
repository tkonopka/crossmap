"""constructing a set of features for a Crossmap analysis
"""

import csv
from collections import Counter
from logging import info
from os.path import exists, basename
from sys import maxsize
from .tokens import CrossmapTokenizer
from .tools import read_dict, write_dict


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
    """count number of times tokens appear in files"""

    counts = Counter()
    ids = set()
    for f in files:
        info("Extracting features from target file: " + basename(f))
        docs = tokenizer.tokenize(f)
        for k, v in docs.items():
            ids.add(k)
            counts.update(list(v.keys()))

    return counts


def feature_map(settings, use_cache=True):
    """get a feature map dictionary

    Parameters
        settings    object of class CrossmapSettings
        use_cache   logical, will try to store/look up features from disk

    Returns
        dictionary with all tokens from target files
        and most common tokens from document files
    """

    cache_file = settings.tsv_file("feature-map")
    if use_cache and exists(cache_file):
        info("Reading feature map from file: " + basename(cache_file))
        result = read_dict(cache_file, value_col="index", value_fun=int)
        info("Feature map size: "+str(len(result)))
        return result

    info("Computing feature map")
    max_features = settings.max_features
    if max_features == 0:
        max_features = maxsize
    info("Max features is "+str(max_features))
    tokenizer = CrossmapTokenizer(settings)
    target_counts = _count_tokens(tokenizer, settings.files("targets"))
    result = dict()
    for k,v in target_counts.items():
        result[k] = len(result)
    if len(result) < max_features:
        doc_counts = _count_tokens(tokenizer, settings.files("documents"))
        for k, v in doc_counts.most_common():
            if len(result) >= max_features:
                break
            if k not in result:
                result[k] = len(result)
    else:
        info("Skipping tokens in documents - maxed out already")

    info("Feature map size: "+str(len(result)))
    if use_cache:
        info("Saving feature map")
        write_dict(result, cache_file, value_col="index")
    return result

