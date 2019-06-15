"""Handling data matrices

@author: Tomasz Konopka
"""

from scipy.sparse import csr_matrix


class CrossmapData:
    """Translator of raw data objects into spare data matrices"""

    def __init__(self, feature_map, tokenizer):
        """intialize with a specific feature set and tokenization strategy

        Arguments:
            feature_map   dict mapping token strings to integers
            tokenizer     configured tokenizer object that will convert
                          documents into weighted sets of tokens
        """

        self.feature_map = feature_map
        self.tokenizer = tokenizer

    def documents(self, filepaths):
        """create a data matrix by parsing data from disk files

        Arguments:
            filepaths     paths to yaml documents

        Returns:
            sparse matrix and a dict mapping ids associated with each matrix row
            array with one string
        """

        data = []
        features = []
        items = [0]
        item_names = dict()
        tokenize = self.tokenizer.tokenize
        feature_map = self.feature_map

        for filepath in filepaths:
            docs = tokenize(filepath)
            for doc_name, tokens in docs.items():
                item_names[doc_name] = len(item_names)
                for k, v in tokens.items():
                    if k not in feature_map:
                        continue
                    data.append(v)
                    features.append(feature_map[k])
                items.append(len(data))

        result = csr_matrix((data, features, items),
                            shape=(len(items)-1, len(feature_map)),
                            dtype=float)
        return result, item_names

    def single(self, dat, aux="", name="X"):
        """create a one-row data matrix by parsing one document object

        Arguments:
            dat            primary data string
            aux            auxiliary string

        Returns:
            sparse matrix with one row
            array with one string
        """

        data = []
        features = []
        feature_map = self.feature_map

        doc = dict(data=dat, auxiliary=aux)
        tokens = self.tokenizer.tokenize_document(doc)
        for k, v in tokens.items():
            if k not in feature_map:
                continue
            data.append(v)
            features.append(feature_map[k])

        result = csr_matrix((data, features, [0, len(data)]),
                            shape=(1, len(feature_map)),
                            dtype=float)
        return result, [name]
