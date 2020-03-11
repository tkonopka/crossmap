"""
Tokenizer for crossmap datasets
"""


import gzip
from math import sqrt
from .tokencounter import TokenCounter
from .tools import yaml_document


def kmers(s, k):
    """create an array with kmers from one string"""

    if len(s) <= k:
        return [s]
    return [s[i:(i+k)] for i in range(len(s)-k+1)]


def token_counts(docs, components=("data", "data_pos", "data_neg")):
    """summarize token counts over all documents"""

    result = TokenCounter()
    for k, v in docs.items():
        for comp in components:
            if comp in v:
                result.update(v[comp])
    return result


def _unit_fun(x):
    """unit function"""
    return x


def _sq_fun(x):
    """square function"""
    return x*x


def _scale_overlap_fun(scale_overlap="sqrt"):
    result = _unit_fun
    if scale_overlap == "sqrt":
        result = sqrt
    elif scale_overlap == "sq":
        result = _sq_fun
    return result


class Kmerizer:
    """A tokenizer of documents that splits words into weighted kmers"""

    def __init__(self, k=(5, 10), case_sensitive=False, alphabet=None):
        """configure a tokenizer

        :param k: pair of integer,
            length of kmers (words will be split into overlapping kmers),
            length of string that should be weighted as a unit.
            If one number is given, the recorded values will be (k, 2*k).
        :param case_sensitive: logical, if False, tokens will be lowercase
        :param alphabet: string with all possible characters
        """

        if type(k) is int or type(k) is float:
            self.k = (int(k), 2*int(k))
        else:
            self.k = (k[0], k[1])
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

    def tokenize(self, doc, scale_fun=sqrt, keys=None):
        """obtain token counts from a single document

        :param doc: dictionary whose content to parse
        :param scale_fun: function
        :param keys: items within the doc to process. Leave None
            to process all the components in doc
        """

        if type(scale_fun) is str:
            scale_fun = _scale_overlap_fun(scale_fun)
        parse = self.parse
        result = dict()
        if keys is None:
            keys = list(doc.keys())
        for k in keys:
            if k not in doc:
                continue
            data = doc[k]
            if type(data) is dict:
                data = [str(v) for v in data.values()]
            result[k] = parse(str(data), scale_fun)
        return result

    def parse(self, s, scale_fun):
        """parse a long string into tokens

        :param s: string
        :param scale_fun: scaling function used for overlapping tokens
        :return: Counter, map from tokens to an adjusted count
        """

        if type(scale_fun) is str:
            scale_fun = _scale_overlap_fun(scale_fun)
        k1 = self.k[0]
        k2 = self.k[1]
        alphabet = self.alphabet
        if not self.case_sensitive:
            s = s.lower()
        result = TokenCounter()
        for word in s.split():
            if not all([_ in alphabet for _ in word]):
                for i in range(len(word)):
                    if word[i] not in alphabet:
                        word = word[:i] + " " + word[(i+1):]
            word = word.strip()
            for sub_word in word.split():
                wlen = len(sub_word)
                weight = scale_fun(max(1.0, wlen/k2) / max(1.0, wlen - k1 + 1))
                for _ in kmers(sub_word, k1):
                    result.add(_.strip(), weight)
        return result


class CrossmapTokenizer(Kmerizer):
    """A Kmerizer with a different constructor"""

    def __init__(self, settings):
        """Create a tokenizer object.

        :param settings: object of class CrossmapSettings
        """

        super().__init__(k=settings.tokens.k,
                         alphabet=settings.tokens.alphabet)

