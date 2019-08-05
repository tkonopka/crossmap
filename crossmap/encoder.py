"""Encoding documents into feature vectors
"""

import numba
from .distance import normalize_vec, vec_norm
from scipy.sparse import csr_matrix


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
        item_names = []
        tokenize = self.tokenizer.tokenize
        encode = self.encode

        for filepath in filepaths:
            docs = tokenize(filepath)
            for doc_name, tokens in docs.items():
                doc_result, _ = encode(tokens, doc_name)
                item_names.append(doc_name)
                data.append(doc_result)

        return data, item_names

    def document(self, doc, name="X"):
        """encode one document into a vector"""

        tokens = self.tokenizer.tokenize_document(doc)
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
            return vec

        data = _to_vec("data")
        aux_pos, aux_neg = _to_vec("aux_pos"), _to_vec("aux_neg")
        w = self.aux_weight
        result = _encode_vec(data, aux_pos, aux_neg, w[0], w[1])
        return csr_matrix(result), name


@numba.jit
def _encode_vec(data, aux_pos, aux_neg, w_pos, w_neg):
    """encode three vectors into one

    Arguments:
        data    numeric vector
        aux_pos numeric vector
        aux_neg numeric vector
        w_pos   numeric value, weight for aux_pos
        w_neg   numeric value, weight for aux_neg

    Returns:
        numeric vector of same length as data
    """

    # regularize weighting using norms
    data_norm = vec_norm(data)
    if data_norm == 0:
        data_norm = 1
    pos_norm = vec_norm(aux_pos)
    neg_norm = vec_norm(aux_neg)
    w_pos = min(w_pos, pos_norm/data_norm)
    w_neg = min(w_neg, neg_norm/data_norm)

    # combine the three vectors into a single normalized vector
    for i in range(len(data)):
        data[i] += w_pos*aux_pos[i] - w_neg*aux_neg[i]
    return normalize_vec(data)

