"""
Encoding documents into feature vectors
"""

import gzip
from math import log2
from numpy import zeros
from .vectors import normalize_vec, add_three
from scipy.sparse import csr_matrix
from .tools import yaml_document


class CrossmapEncoder:
    """Processing of raw data objects into feature vectors"""

    def __init__(self, feature_map, tokenizer, aux_weight=(0.5, 0.5)):
        """intialize with a specific feature set and tokenization strategy

        Arguments:
            feature_map   dict mapping token strings to integers
            tokenizer     configured tokenizer object that will convert
                          documents into weighted sets of tokens
            aux_weight    numeric, weight given to features in "aux" fields
        """

        self.feature_map = feature_map
        self.tokenizer = tokenizer
        self.aux_weight = aux_weight
        self.inv_feature_map = [''] * len(self.feature_map)
        for k, v in feature_map.items():
            self.inv_feature_map[v[0]] = k

    def documents(self, filepaths, scale_fun="sqrt"):
        """generator to parsing data from disk files

        :param filepaths: paths to yaml documents
        :param scale_fun: string, scaling type
        :return: array with encoded  matrix and a dict mapping ids
            associated with each matrix row array with one string
        """

        tokenize = self.tokenizer.tokenize
        encode = self.encode

        if type(filepaths) is str:
            filepaths = [filepaths]

        for filepath in filepaths:
            open_fn = gzip.open if filepath.endswith(".gz") else open
            with open_fn(filepath, "rt") as f:
                for id, doc in yaml_document(f):
                    tokens = encode(tokenize(doc, scale_fun))
                    title = doc["title"] if "title" in doc else ""
                    yield tokens, id, title

    def document(self, doc, scale_fun="sqrt"):
        """encode one document into a vector"""

        tokens = self.tokenizer.tokenize(doc, scale_fun)
        return self.encode(tokens)

    def encode(self, tokens):
        """encode one document into a vector

        :param tokens: dictionary with tokens for data, aux_pos, aux_neg
        :return: array with a vector representation of the data
        """

        feature_map = self.feature_map
        data = _to_vec(tokens, "data_pos", feature_map)
        if "data_pos" not in tokens:
            if "data" in tokens:
                data = _to_vec(tokens, "data", feature_map)
        if "data_neg" in tokens:
            data -= _to_vec(tokens, "data_neg", feature_map)
        return csr_matrix(normalize_vec(data))


def _to_vec(tokens, component, feature_map):
    """helper to transfer from a TokenCounter into a vector

    :param tokens: a dict of TokenCounters
    :param component: a key in the tokens dict
    :param feature_map: dictionary mapping from keys to an index and weight
    :return: an array with dense vector
    """

    vec = zeros(len(feature_map), dtype=float)
    if component not in tokens:
        return vec
    component_data = tokens[component]
    for k, v in component_data.data.items():
        c = component_data.count[k]
        if k not in feature_map:
            continue
        fm = feature_map[k]
        if c == 1:
            vec[fm[0]] = fm[1] * v
        else:
            vec[fm[0]] = fm[1] * (v/c) * (1 + log2(c))

    return vec

