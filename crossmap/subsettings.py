"""
Small classes for capturing small sets of settings for specialized contexts
"""

from os.path import join
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
        result = "Crossmap Kmer Settings:"
        result += "\nk=" + str(self.k)
        result += "\nalphabet='" + str(self.alphabet)
        return result


class CrossmapFeatureSettings:
    """Container for settings related to features"""

    def __init__(self, config=None, data_dir=None):
        self.max_number = 0
        self.weighting = [1, 0]
        self.aux = (0.5, 0.5)
        self.map_file = None

        if config is None:
            return
        for key, val in config.items():
            if key == "max_number":
                self.max_number = int(val)
            elif key == "weighting":
                self.weighting = [float(_) for _ in val]
            elif key == "aux":
                self.aux = [float(_) for _ in val]
            elif key == "map":
                map_file = val
                if data_dir is not None:
                    map_file = join(data_dir, val)
                self.map_file = map_file

    def __str__(self):
        result = "Crossmap Feature Settings:\n"
        result += "max_number=" + str(self.max_number) + ", "
        result += "weighting='" + str(self.weighting) + "', "
        result += "aux_weight=" + str(self.aux)
        return result


class CrossmapDiffusionSettings:
    """Settings for handling diffusion of feature values"""

    def __init__(self, config=None):
        self.threshold = 0.0

        if config is None:
            return
        for key, val in config.items():
            if key == "threshold":
                self.threshold = float(val)

    def __str__(self):
        result = "Crossmap Diffusion Settings:\n"
        result += "threshold=" + str(self.threshold)
        return result


class CrossmapLoggingSettings:
    """Settings for handling diffusion of feature values"""

    def __init__(self, config=None):
        self.level = "WARNING"
        self.progress = pow(10, 5)

        if config is None:
            return
        for key, val in config.items():
            if key == "level":
                self.level = val
            elif key == "progress":
                self.progress = int(val)

    def __str__(self):
        result = "Crossmap Logging Settings:"
        result += "\nlevel=" + str(self.level)
        result += "\nprogress=" + str(self.progress)
        return result


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
        result = "Crossmap Server Settings:"
        result += "\napi_port=" + str(self.api_port)
        result += "\nui_port=" + str(self.ui_port)
        return result


class CrossmapCacheSettings:
    """Settings for cache sizes"""

    def __init__(self, config=None):
        self.counts = 32768
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

    def __str__(self):
        result = "Crossmap Cache Settings:"
        result += "\ncounts=" + str(self.counts)
        result += "\ntitles=" + str(self.titles)
        result += "\nids=" + str(self.ids)
        return result

