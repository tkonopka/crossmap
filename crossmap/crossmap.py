"""Crossmap class
"""

import logging
import functools
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

    def __init__(self, config):
        """configure a crossmap object.

        Arguments:
            config  path to a directory containing crossmap.yaml or a
                    yaml configuration file
        """

        settings = CrossmapSettings(config)
        self.settings = settings
        if not settings.valid:
            return
        self.indexer = CrossmapIndexer(settings)

    def valid(self):
        """get a boolean stating whether settings are valid"""
        return self.settings.valid
