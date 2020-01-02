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

    def __init__(self, k=5, case_sensitive=False, alphabet=None, k2=None):
        """configure a tokenizer

        :param k: integer, length of kmers (words will be split into
            overlapping kmers)
        :param case_sensitive: logical, if False, tokens will be lowercase
        :param alphabet: string with all possible characters
        :param k2: integer, length of kmers used in overlap weighting
        """

        self.k = k
        self.k2 = k2 if k2 is not None else 2*k
        self.case_sensitive = case_sensitive
        if alphabet is None:
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
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

    def tokenize(self, doc, scale_overlap="sqrt"):
        """obtain token counts from a single document"""

        scale_fun = _unit_fun
        if scale_overlap == "sqrt":
            scale_fun = sqrt
        elif scale_overlap == "sq":
            scale_fun = _sq_fun

        parse = self.parse
        result = dict()
        for k, data in doc.items():
            result[k] = parse(str(data), scale_fun)
        return result

    def parse(self, s, scale_fun):
        """parse a long string into tokens

        :param s: string
        :param scale_fun: scaling function, used for overlapping tokens
        :return: Counter, map from tokens to a scaling-adjusted count
        """

        k = self.k
        k2 = self.k2
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
            weight = scale_fun(max(1.0, wlen/k2) / max(1.0, wlen - k + 1))
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


def _unit_fun(x):
    """unit function"""
    return x


def _sq_fun(x):
    """square function"""
    return x*x

