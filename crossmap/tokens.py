"""
Tokenizer for crossmap datasets
"""


import gzip
from math import sqrt
from collections import Counter
from .tools import yaml_document


def kmers(s, k):
    """create an array with kmers from one string"""

    if len(s) <= k:
        return [s]
    return [s[i:(i+k)] for i in range(len(s)-k+1)]


def token_counts(docs, components=("data", "aux_pos", "aux_neg")):
    """summarize token counts over all documents"""

    result = Counter()
    for k, v in docs.items():
        for comp in components:
            if comp in v:
                result.update(v[comp])
    return result


class Kmerizer:
    """A tokenizer of documents that splits words into kmers"""

    def __init__(self, k=5, case_sensitive=False, alphabet=None):
        """configure a tokenizer

        Arguments:
            k               length of kmers (words will be split into overlapping kmers)
            case_sensitive  logical, if False, all tokens will be lowercase
            alphabet        string with all possible characters
        """

        self.k = k
        self.case_sensitive = case_sensitive
        if alphabet is None:
            alphabet =  "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            alphabet += "abcdefghijklmnopqrstuvwxyz"
            alphabet += "0123456789-"
        if not case_sensitive:
            alphabet = alphabet.lower()
        self.alphabet = set([_ for _ in alphabet])

    def tokenize_path(self, filepath):
        """generator for ids and tokens from a data file

        :param filepath: path with yaml content
        :return: id and tokens from each document in the file
        """

        tokenize = self.tokenize
        open_fn = gzip.open if filepath.endswith(".gz") else open
        with open_fn(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                yield id, tokenize(doc)

    def tokenize(self, doc):
        """obtain token counts from a single document"""

        parse = self.parse
        result = dict()
        for k, data in doc.items():
            result[k] = parse(str(data))
        return result

    def parse(self, s):
        """parse a long string into tokens"""

        k = self.k
        alphabet = self.alphabet
        if not self.case_sensitive:
            s = s.lower()
        result = Counter()
        for word in s.split():
            if not all([_ in alphabet for _ in word]):
                for i in range(len(word)):
                    if word[i] not in alphabet:
                        word = word[:i] + " " + word[(i+1):]
            word = word.strip()
            if word == "":
                continue
            wlen = len(word)
            weight = sqrt(max(1.0, wlen/k) / max(1.0, wlen - k + 1))
            for _ in kmers(word, k):
                result[_.strip()] += weight
        return result


class CrossmapTokenizer(Kmerizer):
    """A Kmerizer with a different constructor"""

    def __init__(self, settings):
        """Create a tokenizer object.

        :param settings: object of class CrossmapSettings
        """
        super().__init__(k=settings.tokens.k,
                         alphabet=settings.tokens.alphabet)

