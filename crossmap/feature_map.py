"""constructing a set of features for a Crossmap analysis
"""

from collections import Counter
from logging import info
from os.path import exists, basename
from .tokens import CrossmapTokenizer
from .tools import read_dict, write_dict


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
        return read_dict(cache_file, value_col="index")

    info("Computing feature map")
    tokenizer = CrossmapTokenizer(settings)
    target_counts = _count_tokens(tokenizer, settings.files("targets"))
    result = dict()
    for k,v in target_counts.items():
        result[k] = len(result)
    if len(result) < settings.max_features:
        doc_counts = _count_tokens(tokenizer, settings.files("documents"))
        for k, v in doc_counts.most_common():
            if len(result) >= settings.max_features:
                break
            if k not in result:
                result[k] = len(result)
    else:
        info("Skipping tokens in documents - maxed out already")

    if use_cache:
        info("Saving feature map into file: " + basename(cache_file))
        write_dict(result, cache_file, value_col="index")
    return result

