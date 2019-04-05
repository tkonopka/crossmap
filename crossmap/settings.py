"""Crossmap settings and validation

@author: Tomasz Konopka
"""

import yaml
import logging
from os import getcwd
from os.path import join, exists, dirname, basename, isdir, realpath
from .tokens import Tokenizer

# a dummy variable that initiates a tokenizer with default parameters
default_tokenizer = Tokenizer()


class CrossmapSettings():
    """Container keeping and validating settings for a Crossmap project"""

    def __init__(self, config):
        """Load and validate settings

        Arguments:
            config    directory or filepath to configuration
        """

        # set defaults
        self.name = "crossmap"
        self.dir = getcwd()
        self.file = "crossmap.yaml"
        self.target = []
        self.universe = []
        self.exclude = []
        self.valid = False
        self.tokens = None

        # change defaults given the input
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
        targets = query_files(self.target, "target", dir=dir)
        result["target"] = all(targets) if len(targets)>0 else False
        if not result["target"]:
            logging.error(emsg + "target objects")

        # tokens to exclude
        excludes = query_files(self.exclude, "exclude", dir=dir)
        result["exclude"] = all(excludes)
        if len(excludes) > 0 and not result["exclude"]:
            logging.error(emsg + "exclude")

        # universe (not required, so missing value generates only warning)
        universe = query_files(self.universe, "universe", dir=dir)
        if len(universe) == 0 or not all(universe):
            logging.warning(emsg + "universe objects")

        return result

    def files(self, file_type):
        if file_type not in set(["target", "exclude", "universe"]):
            return []
        return [join(self.dir, _) for _ in self.__dict__[file_type]]

    def token_property(self, s):
        if self.tokens is None:
            return default_tokenizer.__dict__[s]
        if s not in self.tokens:
            return default_tokenizer.__dict__[s]
        return self.tokens[s]

    @property
    def token_min_length(self):
        return self.token_property("min_length")

    @property
    def token_max_length(self):
        return self.token_property("max_length")

    @property
    def token_aux_weight(self):
        return self.token_property("aux_weight")

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

