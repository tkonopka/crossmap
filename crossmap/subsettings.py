"""
Small classes for capturing small sets of settings for specialized contexts
"""

from os.path import join
from yaml import dump
from .tokens import Kmerizer


# a tokenizer with default parameters
default_tokenizer = Kmerizer()


class CrossmapTokenSettings():
    """Container for settings for kmer-based tokenizer"""

    def __init__(self, config=None):
        self.k = 5
        self.alphabet = None

        if config is not None:
            for key, val in config.items():
                if key == "k":
                    self.k = int(val)
                if key == "alphabet":
                    self.alphabet = val

    def __str__(self):
        result = dict(tokens={"k": self.k, "alphabet": self.alphabet})
        return dump(result)


class CrossmapFeatureSettings:
    """Container for settings related to features"""

    def __init__(self, config=None, data_dir=None):
        self.max_number = 0
        self.min_count = 1
        self.weighting = [1, 0]
        self.map_file = None

        if config is None:
            return
        for key, val in config.items():
            if key == "max_number":
                self.max_number = int(val)
            elif key == "min_count":
                self.min_count = int(val)
            elif key == "weighting":
                self.weighting = [float(_) for _ in val]
            elif key == "map":
                map_file = val
                if data_dir is not None:
                    map_file = join(data_dir, val)
                self.map_file = map_file

    def __str__(self):
        result = dict(features={"max_number": self.max_number,
                                "min_count": self.min_count,
                                "weighting": self.weighting,
                                "map_file": self.map_file})
        return dump(result)


class CrossmapIndexingSettings:
    """Container for settings indexing and search quality"""

    def __init__(self, config=None):
        self.build_quality = 200
        self.search_quality = 200

        if config is None:
            return
        for key, val in config.items():
            if key == "build_quality":
                self.build_quality = int(val)
            elif key == "search_quality":
                self.search_quality = int(val)

    def __str__(self):
        result = dict(indexing={"build_quality": self.build_quality,
                                "search_quality": self.search_quality})
        return dump(result)


class CrossmapDiffusionSettings:
    """Settings for handling diffusion of feature values"""

    def __init__(self, config=None):
        self.threshold = 0.0
        self.num_passes = 2

        if config is None:
            return
        for key, val in config.items():
            if key == "threshold":
                self.threshold = float(val)
            if key == "passes":
                self.num_passes = int(val)

    def __str__(self):
        result = dict(diffusion={"threshold": self.threshold,
                                 "passes": self.num_passes})
        return dump(result)


class CrossmapLoggingSettings:
    """Settings for handling diffusion of feature values"""

    def __init__(self, config=None):
        self.level = "WARNING"
        self.progress = 2*pow(10, 5)

        if config is None:
            return
        for key, val in config.items():
            if key == "level":
                self.level = str(val)
            elif key == "progress":
                self.progress = int(val)

    def __str__(self):
        result = dict(logging={"level": self.level,
                               "progress": self.progress})
        return dump(result)


class CrossmapServerSettings:
    """Container for settings for server"""

    def __init__(self, config=None):
        self.api_port = 8098
        self.ui_port = 8099

        if config is None:
            return
        for key, val in config.items():
            if key == "api_port":
                self.api_port = int(val)
            elif key == "ui_port":
                self.ui_port = int(val)

    def __str__(self):
        result = dict(server={"api_port": self.api_port,
                              "ui_port": self.ui_port})
        return dump(result)


class CrossmapCacheSettings:
    """Settings for cache sizes"""

    def __init__(self, config=None):
        self.counts = 16384
        self.data = 16384
        self.ids = 8192
        self.titles = 4096

        if config is None:
            return
        for key, val in config.items():
            if key == "counts":
                self.counts = int(val)
            elif key == "ids":
                self.ids = int(val)
            elif key == "titles":
                self.titles = int(val)
            elif key == "data":
                self.data = int(val)

    def __str__(self):
        result = dict(cache={"counts": self.counts,
                             "titles": self.titles,
                             "ids": self.ids,
                             "data": self.data})
        return dump(result)

