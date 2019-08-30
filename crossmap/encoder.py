"""Encoding documents into feature vectors
"""

import gzip
from .distance import normalize_vec
from scipy.sparse import csr_matrix
from .tools import yaml_document


class CrossmapEncoder:
    """Processing of raw data objects into feature vectors"""

    def __init__(self, feature_map, tokenizer, aux_weight=[0.5, 0.5]):
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

    def documents(self, filepaths):
        """create a data matrix by parsing data from disk files

        Arguments:
            filepaths     paths to yaml documents

        Returns:
            array with encoded  matrix and a dict mapping ids associated with each matrix row
            array with one string
        """

        data = []
        ids_titles = []
        tokenize = self.tokenizer.tokenize
        encode = self.encode

        for filepath in filepaths:
            open_fn = gzip.open if filepath.endswith(".gz") else open
            with open_fn(filepath, "rt") as f:
                for id, doc in yaml_document(f):
                    tokens, _ = encode(tokenize(doc), id)
                    title = doc["title"] if "title" in doc else ""
                    ids_titles.append([id, title])
                    data.append(tokens)

        return data, ids_titles

    def document(self, doc, name="X"):
        """encode one document into a vector"""

        tokens = self.tokenizer.tokenize(doc)
        return self.encode(tokens, name)

    def encode(self, tokens, name="X"):
        """encode one document into a vector

        Arguments:
            tokens         a dictionary with tokens for data, aux_pos, aux_neg
            name           character, default name for this object

        Returns:
            array with weights for all features based on doc
            one string
        """

        feature_map = self.feature_map
        n_features = len(feature_map)

        def _to_vec(component):
            """helper to transfer from a dict/counter into a vector"""
            vec = [0.0]*n_features
            if component not in tokens:
                return vec
            for k, v in tokens[component].items():
                if k not in feature_map:
                    continue
                fm = feature_map[k]
                vec[fm[0]] += fm[1]*v
            return normalize_vec(vec)

        data = _to_vec("data")
        aux_pos, aux_neg = _to_vec("aux_pos"), _to_vec("aux_neg")
        w = self.aux_weight
        result = data
        for i in range(len(data)):
            result[i] += w[0]*aux_pos[i] - w[1]*aux_neg[i]
        return csr_matrix(normalize_vec(result)), name

