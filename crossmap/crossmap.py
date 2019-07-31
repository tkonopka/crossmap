"""Crossmap class
"""

import functools
from logging import info
from os import mkdir
from os.path import exists
from .settings import CrossmapSettings
from .indexer import CrossmapIndexer
from .tools import open_file, yaml_document


def require_valid(function):
    """Decorator, check if class is .valid before computation."""

    @functools.wraps(function)
    def wrapped(self, *args, **kw):
        if self.valid():
            return function(self, *args, **kw)
        return None

    return wrapped


def prediction(ids, distances, name):
    """structure an object describing a nn prediction"""
    return dict(query=name, targets=ids, distances=distances)


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

    @property
    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid

    def build(self):
        """create indexes and auxiliary objects"""
        self.indexer.build()
        self.indexer.db.index()

    def load(self):
        """load indexes from prepared files"""
        self.indexer.load()

    def predict(self, doc, n=3, query_name="query"):
        """predict nearest targets for one document

        Arguments:
            doc   dict-like object with "data", "aux_pos" and "aux_neg"
            n     integer, number of neighbors

        Returns:
            two lists.
            First list contains target ids
            Second list contains weighted distances
        """

        doc_data = self.indexer.encode(doc)
        targets, distances = self.indexer.suggest_targets(doc_data, n)
        return prediction(targets[:n], distances[:n], query_name)

    def predict_file(self, filepath, n=3):
        """predict nearest targets for documents defined in a file

        Arguments:
            docs    dict mapping query ids to query documents
            n       integer, number of neighbors

        Returns:
            one list with composite objects
        """

        result = []
        with open_file(filepath, "rt") as f:
            for id, doc in yaml_document(f):
                result.append(self.predict(doc, n, id))
        return result
