"""
Encoding documents into feature vectors
"""

import gzip
from math import log2
from numpy import array
from .csr import normalize_csr
from .sparsevector import Sparsevector
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
        inv_map = [''] * len(feature_map)
        for k, v in feature_map.items():
            inv_map[v[0]] = k
        self.inv_feature_map = inv_map

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
        result = Sparsevector()
        if "data" in tokens:
            i, v = _text_to_vec(tokens["data"], feature_map)
            result.add(i, v)
        if "data_pos" in tokens:
            i, v = _text_to_vec(tokens["data_pos"], feature_map)
            result.add(i, v)
        if "data_neg" in tokens:
            i, v = _text_to_vec(tokens["data_neg"], feature_map)
            result.add(i, -v)
        if values is not None:
            i, v = _vector_to_vec(values, feature_map)
            result.add(i, v)
        return normalize_csr(result.to_csr(len(feature_map)))


def _text_to_vec(tokencounter, feature_map):
    """transfer from a TokenCounter into a vector

    :param tokencounter: a TokenCounter object
    :param feature_map: dictionary mapping from keys to an index and weight
    :return: indices and values for a csr object
    """

    data, counts = tokencounter.data, tokencounter.count
    indices, values = [], []
    for k, v in data.items():
        ck = counts[k]
        try:
            k_index, k_weight = feature_map[k]
        except KeyError:
            # skips tokens that are not in the feature map
            # the try/except construct is faster than
            # if k not in feature_map: continue
            continue
        # these two branches are equivalent, but the first branch is a shortcut
        # for a common case
        indices.append(k_index)
        if ck == 1:
            values.append(k_weight * v)
        else:
            values.append(k_weight * (v/ck) * (1 + log2(ck)))
    return indices, array(values)


def _vector_to_vec(d, feature_map):
    """transfer from a TokenCounter into a vector

    :param d: a dict mapping features to values
    :param feature_map: dictionary mapping from keys to an index and weight
    :return: indices and values for a csr object
    """

    indices, values = [], []
    for k, v in d.items():
        if k not in feature_map:
            continue
        ki, kw = feature_map[k]
        indices.append(ki)
        values.append(kw*v)
    return indices, array(values)

