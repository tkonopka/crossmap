"""Tokenizer specifically for crossmap datasets.

@author: Tomasz Konopka
"""


import gzip
import re
from collections import Counter
from .tools import read_set, yaml_document


class Tokenizer():

    def __init__(self, include=None, exclude=None, aux_weight=0.5,
                 min_length=3, max_length=12, case_sensitive=False):
        """configure a tokenizer

        Arguments:
            include         path to text file with tokens to include
            exclude         path to text file with tokens to exclude
            aux_weight      numeric, weighting for auxiliary tokens
            min_length      minimum number of characters in final token
            max_length      maximum number of characters in tokens
            case_sensitive  logical, if False, all tokens will be lowercase
        """

        # for cleaning raw tokens
        self.cleaning = ["/|\\.|\\[|]|,|:|;|!|<|>|%|'|\\?|\"", "\\(|\\)",
                         "±|·|=|\+", "[0-9]+", "^_|_$", "s$", "-$|^-"]
        # minimum/maximum number of characters (longer token will be split)
        self.min_length = min_length
        self.max_length = max_length
        self.case_sensitive = case_sensitive
        # weighting of auxiliary/primary tokens
        self.aux_weight = aux_weight
        # get sets of tokens to include/exclude
        self.include = read_set(include)
        self.exclude = read_set(exclude)

    def tokenize(self, filepath):
        """scan context of a dataset file and return a tokens dict

        Returns:
            dict mapping object ids to Counter object with token counts
        """

        result = dict()
        open_fn = gzip.open if filepath.endswith(".gz") else open
        with open_fn(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result[id] = self._tokens(doc)

        return result

    def _tokens(self, doc):
        """obtain token counts from a single document"""

        # get tokens from primary and auxiliary fields
        data, aux = Counter(), Counter()
        if "data" in doc:
            data = Counter(self.parse(doc["data"]))
        if "auxiliary" in doc:
            aux = Counter(self.parse(doc["auxiliary"]))

        # assemble weighted tokens into a single element
        result = dict()
        aux_weight = self.aux_weight
        for k, v in data.items():
            result[k] = v
        for k, v in aux.items():
            if k not in result:
                result[k] = 0
            result[k] += v * aux_weight
        return result

    def parse(self, s):
        """parse a long string into tokens"""

        tokens = self._clean_tokens(s.split())
        # process tokens for length
        minlen = self.min_length
        exclude = self.exclude
        tokens = [_ for _ in tokens if len(_) >= minlen]
        if not self.case_sensitive:
            tokens = [_.lower() for _ in tokens]
        tokens = [_ for _ in tokens if _ not in exclude]
        return tokens

    def _clean_tokens(self, tokens):
        """apply regex cleaning to tokens"""

        patterns = self.cleaning
        resub = re.sub
        for p in patterns:
            tokens = [resub(p, "", _) for _ in tokens]
        tokens = [resub("--", "-", _) for _ in tokens]
        return tokens


def token_counts(docs):
    """summarize token counts over all documents"""

    result = Counter()
    for k, v in docs.items():
        result.update(v)
    return result

