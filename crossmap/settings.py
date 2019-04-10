"""Crossmap settings and validation

@author: Tomasz Konopka
"""

import yaml
import logging
from os import getcwd
from os.path import join, exists, dirname, basename, isdir
from .tokens import Tokenizer

# a tokenizer with default parameters
default_tokenizer = Tokenizer()


class CrossmapTokenSettings():
    """Container for settings for tokenizer"""

    def __init__(self, config=None):
        self.min_length = 3
        self.max_length = 10

        if config is not None:
            for k, v in config.items():
                if k == "min_length":
                    self.min_length = v
                if k == "max_length":
                    self.max_length = v

    def valid(self):
        return True


class CrossmapUmapSettings():
    """Container for umap settings"""

    def __init__(self, config=None):
        self.n_components = 2
        self.n_neighbors = 15
        self.metric = "cosine"

        if config is not None:
            for k, v in config.items():
                if k == "n_components":
                    self.n_components = v
                if k == "n_neighbors":
                    self.n_neighbors = v
                if k == "metric":
                    self.metric = v

    def valid(self):
        return True


class CrossmapSettingsDefaults:
    """Container defining all settings for a crossmap project"""

    def __init__(self):
        self.name = "crossmap"
        self.dir = getcwd()
        self.file = "crossmap.yaml"
        self.targets = []
        self.documents = []
        self.exclude = []
        self.valid = False
        # tuning
        self.max_features = 0
        self.aux_weight = 0.5
        # sub-settings for components: tokens and embedding
        self.tokens = CrossmapTokenSettings()
        self.umap = CrossmapUmapSettings()


class CrossmapSettings(CrossmapSettingsDefaults):
    """Container keeping and validating settings for a Crossmap project"""

    def __init__(self, config):
        """Load and validate settings

        Arguments:
            config    directory or filepath to configuration
        """

        super().__init__()
        if config is not None:
            if isdir(config):
                self.dir = config
            else:
                self.dir = dirname(config)
                self.file = basename(config)
        if self.dir == "":
            self.dir = getcwd()

        if self._load(self.dir, self.file):
            self.valid = all(list((self._validate()).values()))

    def _load(self, dirpath, filename):
        """load settings from a file, return True/False of success"""

        filepath = join(dirpath, filename)
        status = require_file(dirpath, "configuration directory")
        status = status and require_file(filepath, "configuration file")
        if not status:
            return False

        with open(filepath, "r") as f:
            result = yaml.safe_load(f)
        for k, v in result.items():
            if k == "tokens":
                self.tokens = CrossmapTokenSettings(v)
            elif k == "umap":
                self.umap = CrossmapUmapSettings(v)
            else:
                self.__dict__[k] = v
        return True

    def _validate(self):
        """perform a series of checks"""

        emsg = "Configuration does not specify "
        result = dict()
        dir = self.dir

        # location and settings file
        result["dir"] = require_file(dir, "configuration directory")
        result["file"] = require_file(join(dir, self.file), "configuration file")
        if not result["dir"] or not result["file"]:
            return result

        # configuration name
        result["name"] = (type(self.name) is str and self.name != "")
        if not result["name"]:
            logging.error(emsg + "valid name")

        # target objects to map toward
        targets = query_files(self.targets, "targets", dir=dir)
        result["targets"] = all(targets) if len(targets) > 0 else False
        if not result["targets"]:
            logging.error(emsg + "target objects")

        # tokens to exclude
        excludes = query_files(self.exclude, "exclude", dir=dir)
        result["exclude"] = all(excludes)
        if len(excludes) > 0 and not result["exclude"]:
            logging.error(emsg + "exclude")

        # universe (not required, so missing value generates only warning)
        documents = query_files(self.documents, "documents", dir=dir)
        if len(documents) == 0 or not all(documents):
            logging.warning(emsg + "document objects")

        return result

    def files(self, file_types):
        """Get paths to project files.

        Argument:
            file_types   an iterable with value "targets", "exclude", "documents"

        Returns:
            simple list with file paths
        """

        if type(file_types) is str:
            file_types = [file_types]

        result = []
        for file_type in file_types:
            if file_type not in set(["targets", "exclude", "documents"]):
                logging.warning("attempting to retrieve unknown file type: "+str(file_type))
                continue
            for _ in self.__dict__[file_type]:
                result.append(join(self.dir, _))
        return result

    def __str__(self):
        """simple view of the object (for debugging)"""
        return str(self.__dict__)


def query_file(filepath, filetype, log=logging.warning):
    """check if a file or directory exists, emit a message if not"""

    if not exists(filepath):
        if log is not None:
            log(filetype + " does not exist: " + filepath)
        return False
    return True


def query_files(filepaths, filetype, log=logging.warning, dir=None):
    """check a list of files using query_file()"""

    if type(filepaths) is str:
        filepaths = [filepaths]
    if dir is not None:
        filepaths = [join(dir, _) for _ in filepaths]
    return [query_file(_, filetype, log) for _ in filepaths]


def require_file(filepath, filetype):
    """check if a file or directory exists, emit a message if not"""

    return query_file(filepath, filetype, log=logging.error)

