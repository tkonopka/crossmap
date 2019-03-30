"""Crossmap class

@author: Tomasz Konopka
"""

from .tokens import Tokenizer, token_counts


class Crossmap():

    def __init__(self, config):
        """configure a crossmap object.

        Arguments:
            config     configuration object
        """

        self.config = config

    def build(self, filepath):
        pass

    def tokens(self):
        """scan context of a dataset file and return a tokens dict"""

        tokenizer = Tokenizer()
        # count all tokens in all documents
        config = self.config
        source_counts = token_counts(tokenizer.tokenize(config.source))
        target_counts = token_counts(tokenizer.tokenize(config.target))
        # identify all tokens in either dataset
        tokens = set()
        tokens.update(source_counts.keys())
        tokens.update(target_counts.keys())
        # write out a summary
        print("token\tsource\ttarget")
        for token in tokens:
            c0 = source_counts.get(token, 0)
            c1 = target_counts.get(token, 0)
            print(token + "\t" + str(c0) + "\t" + str(c1))
