"""Encoding documents into feature vectors
"""


class CrossmapEncoder:
    """Processing of raw data objects into feature vectors"""

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
            array with encoded  matrix and a dict mapping ids associated with each matrix row
            array with one string
        """

        data = []
        item_names = []
        tokenize = self.tokenizer.tokenize
        feature_map = self.feature_map

        for filepath in filepaths:
            docs = tokenize(filepath)
            for doc_name, tokens in docs.items():
                item_names.append(doc_name)
                item_data = [0.0]*len(feature_map)
                for k, v in tokens.items():
                    if k not in feature_map:
                        continue
                    item_data[feature_map[k]] += v
                data.append(item_data)

        return data, item_names

    def encode(self, doc, name="X"):
        """encode one document into a vector

        Arguments:
            doc            a dictionary with data, aux_pos, aux_neg
            name           character, default name for this object

        Returns:
            array with weights for all features based on doc
            one string
        """

        feature_map = self.feature_map
        data = [0.0]*len(feature_map)

        tokens = self.tokenizer.tokenize_document(doc)
        for k, v in tokens.items():
            if k not in feature_map:
                continue
            data[feature_map[k]] += v

        return data, name

