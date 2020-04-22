"""
Encoding documents into feature vectors
"""

import gzip
from math import log2
from numpy import zeros
from .csr import normalize_csr, csr_vector
from .tools import yaml_document


class CrossmapEncoder:
    """Processing of raw data objects into feature vectors"""

    data_fields = ("data", "data_pos", "data_neg")

    def __init__(self, feature_map, tokenizer):
        """initialize with a specific feature set and tokenization strategy

        :param feature_map: dict mapping token strings to integers
        :param tokenizer:   configured tokenizer object that can convert
            documents into weighted sets of tokens
        """

        self.feature_map = feature_map
        self.tokenizer = tokenizer
        self.inv_feature_map = [''] * len(self.feature_map)
        for k, v in feature_map.items():
            self.inv_feature_map[v[0]] = k

    def documents(self, filepaths, tokenizer=None):
        """generator to parsing data from disk files

        :param filepaths: paths to yaml documents
        :param tokenizer: Kmerizer, if None defaults to self.tokenizer
        :return: 3-tuple with id, entire document, and an encoding
        """

        encode_document = self.document
        if tokenizer is None:
            tokenizer = self.tokenizer
        if type(filepaths) is str:
            filepaths = [filepaths]
        for filepath in filepaths:
            open_fn = gzip.open if filepath.endswith(".gz") else open
            with open_fn(filepath, "rt") as f:
                for id, doc in yaml_document(f):
                    result = encode_document(doc, tokenizer)
                    yield id, doc, result

    def document(self, doc, tokenizer=None):
        """encode one document into a vector"""

        if tokenizer is None:
            tokenizer = self.tokenizer
        tokens = tokenizer.tokenize(doc, self.data_fields)
        # simple way out - document only has text data
        if "values" not in doc:
            return self._encode(tokens, None)
        # convert a key-value dictionary into feature-value dictionary
        values = dict()
        parse = tokenizer.parse
        for k, v in doc["values"].items():
            v_float = float(v)
            features = parse(k)
            for f in features.keys():
                if f not in values:
                    values[f] = 0
                values[f] += v_float * features.data[f]
        return self._encode(tokens, values)

    def _encode(self, tokens, values=None):
        """encode one document into a vector

        :param tokens: dictionary with tokens for data, data_pos, data_neg
        :param values: dictionary with mapping from feature to value
        :return: array with a vector representation of the data
        """

        feature_map = self.feature_map
        data = zeros(len(feature_map), dtype=float)
        if "data" in tokens:
            data += _text_to_vec(tokens, "data", feature_map)
        if "data_pos" in tokens:
            data += _text_to_vec(tokens, "data_pos", feature_map)
        if "data_neg" in tokens:
            data -= _text_to_vec(tokens, "data_neg", feature_map)
        if values is not None:
            data += _vector_to_vec(values, feature_map)
        return normalize_csr(csr_vector(data))


def _text_to_vec(tokens, component, feature_map):
    """transfer from a TokenCounter into a vector

    :param tokens: a dict of TokenCounters
    :param component: a key in the tokens dict
    :param feature_map: dictionary mapping from keys to an index and weight
    :return: an array with dense vector
    """

    result = zeros(len(feature_map), dtype=float)
    component_data = tokens[component].data
    component_counts = tokens[component].count
    for k, v in component_data.items():
        c = component_counts[k]
        try:
            k_index, k_weight = feature_map[k]
        except KeyError:
            # skips tokens that are not in the feature map
            # the try/except construct is faster than
            # if k not in feature_map: continue
            continue
        # these two branches are equivalent, but the first branch is a shortcut
        # for a common case
        if c == 1:
            result[k_index] = k_weight * v
        else:
            result[k_index] = k_weight * (v/c) * (1 + log2(c))
    return result


def _vector_to_vec(values, feature_map):
    """transfer from a TokenCounter into a vector

    :param values: a dict mapping features to values
    :param feature_map: dictionary mapping from keys to an index and weight
    :return: an array with dense vector
    """

    result = zeros(len(feature_map), dtype=float)
    for k, v in values.items():
        if k not in feature_map:
            continue
        ki, kw = feature_map[k]
        result[ki] = kw * v
    return result

