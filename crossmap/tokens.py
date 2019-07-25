"""Tokenizer specifically for crossmap datasets.
"""


import gzip
from collections import Counter
from .tools import yaml_document


def kmers(s, k):
    """create an array with kmers from one string"""

    if len(s) <= k:
        return [s]
    return [s[i:(i+k)] for i in range(len(s)-k+1)]


class Kmerizer():
    """A tokenizer of documents that splits words into kmers"""

    def __init__(self, aux_weight=0.5, k=5, case_sensitive=False, alphabet=None):
        """configure a tokenizer

        Arguments:
            aux_weight      numeric, weighting for auxiliary tokens
            k               length of kmers (words will be split into overlapping kmers)
            case_sensitive  logical, if False, all tokens will be lowercase
            alphabet        string with all possible characters
        """

        self.aux_weight = aux_weight
        self.k = k
        self.case_sensitive = case_sensitive
        if alphabet is None:
            alphabet =  "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            alphabet += "abcdefghijklmnopqrstuvwxyz"
            alphabet += "0123456789-"
        if not case_sensitive:
            alphabet = alphabet.lower()
        self.alphabet = set([_ for _ in alphabet])

    def tokenize(self, filepath):
        """scan context of a dataset file and return a tokens dict

        Returns:
            dict mapping object ids to Counter object with token values
        """

        result = dict()
        tokenize_doc = self.tokenize_document
        open_fn = gzip.open if filepath.endswith(".gz") else open
        with open_fn(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result[id] = tokenize_doc(doc)
        return result

    def tokenize_document(self, doc):
        """obtain token counts from a single document"""

        # count raw tokens in primary and auxiliary fields
        data, aux = Counter(), Counter()
        if "data" in doc:
            data = Counter(self.parse(doc["data"]))
        if "auxiliary" in doc:
            aux = Counter(self.parse(doc["auxiliary"]))

        # assemble weighted tokens into a single element
        result = dict(data)
        weight = self.aux_weight
        for k, v in aux.items():
            if k not in result:
                result[k] = 0
            result[k] += v * weight
        return result

    def parse(self, s):
        """parse a long string into tokens"""

        k = self.k
        alphabet = self.alphabet
        if not self.case_sensitive:
            s = s.lower()
        result = []
        for word in s.split():
            for i in range(len(word)):
                if word[i] not in alphabet:
                    word = word[:i]+" "+word[(i+1):]
            result.extend(kmers(word.strip(), k))
        return result


def token_counts(docs):
    """summarize token counts over all documents"""

    result = Counter()
    for k, v in docs.items():
        result.update(v)
    return result

