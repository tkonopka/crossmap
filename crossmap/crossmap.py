"""Crossmap class

@author: Tomasz Konopka
"""

import logging
from os.path import join, exists, basename
from .tokens import Tokenizer
from .settings import CrossmapSettings


class Crossmap():

    def __init__(self, config):
        """configure a crossmap object.

        Arguments:
            config  path to a directory containing crossmap.yaml or an
                    appropriate yaml configuration file
        """

        settings = CrossmapSettings(config)
        self.settings = settings
        self.tokenizer = Tokenizer(min_length=settings.token_min_length,
                                   max_length=settings.token_max_length,
                                   aux_weight=settings.token_aux_weight,
                                   exclude=settings.files("exclude"))

    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid

    def build(self):
        target_tokens = self.target_tokens()

    def _txtfile(self, label):
        """create a project txt filepath"""

        s = self.settings
        return join(s.dir, s.name + "-" + label + ".txt")

    def target_tokens(self):
        """scan target documents to collect target tokens"""

        tok_file = self._txtfile("target-tokens")
        if exists(tok_file):
            logging.info("Reading target tokens  (" + basename(tok_file)+")")
            with open(tok_file, "rt") as f:
                result = f.readlines()
            return set([_.strip() for _ in result])

        settings, tokenizer = self.settings, self.tokenizer
        tokens = set()
        for target_file in settings.files("target"):
            logging.info("Extracting target tokens: " + basename(target_file))
            docs = tokenizer.tokenize(target_file)
            for k, v in docs.items():
                tokens.update(v.keys())
        with open(tok_file, "wt") as f:
            f.write("\n".join(tokens))

        return tokens
