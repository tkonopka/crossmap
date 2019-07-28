"""Crossmap class
"""

import logging
import functools
from os import mkdir
from os.path import exists
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer


def require_valid(function):
    """Decorator, check if class is .valid before computation."""

    @functools.wraps(function)
    def wrapped(self, *args, **kw):
        if self.valid():
            return function(self, *args, **kw)
        return None

    return wrapped


class Crossmap():

    def __init__(self, settings):
        """configure a crossmap object.

        Arguments:
            config  path to a directory containing config-simple.yaml or a
                    yaml configuration file
        """

        if type(settings) is str:
            settings = CrossmapSettings(settings)
        self.settings = settings
        if not settings.valid:
            return

        # ensure directories exist
        if not exists(self.settings.data_dir):
            mkdir(self.settings.data_dir)

        # prepare objects
        self.indexer = CrossmapIndexer(settings)
        self.encoder = self.indexer.encoder

    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid

    def build(self):
        """create indexes and auxiliary objects"""
        self.indexer.build()

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()

    def predict(self, doc, n=3):
        """predict nearest target"""

        doc_data = self.indexer.encode(doc)
        targets, distances = self.indexer.suggest_targets(doc_data, n)
        return targets[:n], distances[:n]

