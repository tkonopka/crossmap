"""Crossmap settings and validation
"""

import yaml
from logging import error, warning
from os import getcwd, mkdir
from os.path import join, exists, dirname, basename, isdir
from .tokens import Kmerizer

# a tokenizer with default parameters
default_tokenizer = Kmerizer()


class CrossmapKmerSettings():
    """Container for settings for kmer-based tokenizer"""

    def __init__(self, config=None):
        self.k = 5
        self.alphabet = None

        if config is not None:
            for key, val in config.items():
                if key == "k":
                    self.k = val
                if key == "alphabet":
                    self.alphabet = val

    def valid(self):
        return True

    def __str__(self):
        result = "Crossmap Kmer Settings:\n"
        result += "k=" + str(self.k) + ", "
        result += "alphabet='" + str(self.alphabet) + "'"
        return result


class CrossmapSettingsDefaults:
    """Container defining all settings for a crossmap project"""

    def __init__(self):
        self.name = ""   # this must be set
        self.dir = getcwd()
        self.data_dir = join(self.dir, self.name)
        self.file = "config-simple.yaml"
        self.targets = []
        self.documents = []
        self.exclude = []
        self.valid = False
        # tuning
        self.max_features = 0
        self.aux_weight = 0.5
        # sub-settings for components: tokens and embedding
        self.tokens = CrossmapKmerSettings()

    def tsv_file(self, label):
        """create a file path for project tsv data"""
        return join(self.data_dir, self.name + "-" + label + ".tsv")

    def pickle_file(self, label):
        """create a file path for project binary data object"""
        return join(self.data_dir, self.name + "-" + label)

    def annoy_file(self, label):
        """create a file path for a project index file"""
        return join(self.data_dir, self.name + "-index-" + label + ".ann")

    def index_file(self, label):
        """create a file path for a project index file"""
        return join(self.data_dir, self.name + "-" + label + "-index")


class CrossmapSettings(CrossmapSettingsDefaults):
    """Container keeping and validating settings for a Crossmap project"""

    def __init__(self, config, create_dir=False):
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

        self.data_dir = join(self.dir, self.name)

        # perhaps create directories exist
        if create_dir and not exists(self.data_dir):
            mkdir(self.data_dir)

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
                self.tokens = CrossmapKmerSettings(v)
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
            error(emsg + "valid name")

        # target objects to map toward
        targets = query_files(self.targets, "targets", dir=dir)
        result["targets"] = all(targets) if len(targets) > 0 else False
        if not result["targets"]:
            error(emsg + "'targets'")

        # tokens to exclude
        excludes = query_files(self.exclude, "exclude", dir=dir)
        result["exclude"] = all(excludes)
        if len(excludes) > 0 and not result["exclude"]:
            error(emsg + "exclude")

        # universe (not required, so missing value generates only warning)
        documents = query_files(self.documents, "documents", dir=dir)
        if len(documents) == 0 or not all(documents):
            warning(emsg + "'documents'")

        return result

    def files(self, file_types):
        """Get paths to project files.

        Argument:
            file_types   an iterable with value "targets", "documents"

        Returns:
            simple list with file paths
        """

        if type(file_types) is str:
            file_types = [file_types]

        result = []
        for file_type in file_types:
            if file_type not in set(["targets", "documents"]):
                warning("attempting to retrieve unknown file type: "+str(file_type))
                continue
            for _ in self.__dict__[file_type]:
                result.append(join(self.dir, _))
        return result

    def __str__(self):
        """simple view of the object (for debugging)"""
        return str(self.__dict__)


def query_file(filepath, filetype, log=warning):
    """check if a file or directory exists, emit a message if not"""

    if not exists(filepath):
        if log is not None:
            log(filetype + " does not exist: " + filepath)
        return False
    return True


def query_files(filepaths, filetype, log=warning, dir=None):
    """check a list of files using query_file()"""

    if type(filepaths) is str:
        filepaths = [filepaths]
    if dir is not None:
        filepaths = [join(dir, _) for _ in filepaths]
    return [query_file(_, filetype, log) for _ in filepaths]


def require_file(filepath, filetype):
    """check if a file or directory exists, emit a message if not"""

    return query_file(filepath, filetype, log=error)

