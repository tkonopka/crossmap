"""
Crossmap settings and validation
"""

import yaml
from logging import error, warning
from os import getcwd, mkdir
from os.path import join, exists, dirname, basename, isdir
from .tokenizer import Kmerizer
from .subsettings import \
    CrossmapLoggingSettings, \
    CrossmapServerSettings, \
    CrossmapFeatureSettings, \
    CrossmapIndexingSettings, \
    CrossmapDiffusionSettings, \
    CrossmapTokenSettings, \
    CrossmapCacheSettings

# a tokenizer with default parameters
default_tokenizer = Kmerizer()


class CrossmapSettingsDefaults:
    """Container defining all settings for a crossmap project"""

    def __init__(self):
        self.name = ""
        self.dir = getcwd()
        self.prefix = join(self.dir, self.name)
        self.file = "crossmap.yaml"
        # paths to disk files
        self.data_files = dict()
        # settings for features (e.g. max number, or from file)
        self.features = CrossmapFeatureSettings()
        # settings for indexing and search quality
        self.indexing = CrossmapIndexingSettings()
        # setting for diffusion
        self.diffusion = CrossmapDiffusionSettings()
        # settings for tokens (e.g. kmer length)
        self.tokens = CrossmapTokenSettings()
        # settings for server (e.g. port)
        self.server = CrossmapServerSettings()
        # for logging and batch splitting
        self.logging = CrossmapLoggingSettings()
        # for runtime performance, caching of db results
        self.cache = CrossmapCacheSettings()
        # summary of state
        self.valid = False
        # misc settings set at runtime
        self.require_data_files = True

    def db_file(self):
        """path to db file"""
        return join(self.prefix, self.name + ".sqlite")

    def yaml_file(self, label):
        """path to manual dataset"""
        return join(self.prefix, self.name + "-" + label + ".yaml")

    def tsv_file(self, label):
        """path for project tsv data"""
        return join(self.prefix, self.name + "-" + label + ".tsv")

    def pickle_file(self, label):
        """path for project binary data object"""
        return join(self.prefix, self.name + "-" + label)

    def index_file(self, label):
        """path for a project indexer file"""
        return join(self.prefix, self.name + "-" + label + "-index")


class CrossmapSettings(CrossmapSettingsDefaults):
    """Container keeping and validating settings for a Crossmap project"""

    def __init__(self, config, create_dir=False, require_data_files=True):
        """create a settings object

        :param config: path to a configuration file
        :param create_dir: logical, create directory automatically
        :param require_data_files: logical, set True to require access to
            original data files. Set to False to allow using a configuration
             despite missing data files.
        """

        super().__init__()
        self.require_data_files = require_data_files
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

        self.prefix = join(self.dir, self.name)

        if create_dir and not exists(self.prefix):
            mkdir(self.prefix)

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
            if k == "data":
                self.data_files = v
            elif k == "tokens":
                self.tokens = CrossmapTokenSettings(v)
            elif k == "features":
                self.features = CrossmapFeatureSettings(v, self.dir)
            elif k == "server":
                self.server = CrossmapServerSettings(v)
            elif k == "diffusion":
                self.diffusion = CrossmapDiffusionSettings(v)
            elif k == "logging":
                self.logging = CrossmapLoggingSettings(v)
            elif k == "cache":
                self.cache = CrossmapCacheSettings(v)
            else:
                self.__dict__[k] = v
        return True

    def _validate(self):
        """perform a series of checks"""

        missing_msg = "Configuration does not specify "
        incorrect_msg = "Configuration mis-specifies "
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
            error(missing_msg + "valid name")

        # data collections
        result["data"] = True
        if self.require_data_files:
            self.data_files, skipped = query_files(self.data_files,
                                                   "data file", dir=dir)
            result["data"] = len(self.data_files) > 0
            if not result["data"]:
                error(missing_msg + "'data'")

        fmf = self.features.map_file
        if fmf is not None:
            result["feature_map"] = query_file(fmf, "feature_map")

        result["weighting"] = True
        if len(self.features.weighting) != 2:
            self.features.weighting = [1, 0]
            warning(incorrect_msg + 'weighting')

        return result

    def __str__(self):
        """simple view of the object (for debugging)"""
        return str(self.__dict__)


def query_file(filepath, filetype, log=warning):
    """assess whether a file is usable or not

    :param filepath: path to file on disk
    :param filetype: string, used in a logging message
    :param log: logging function
    :return: Logical value depending on whether a file is usable or not
    """

    if not exists(filepath):
        if log is not None:
            log(filetype + " does not exist: " + filepath)
        return False
    return True


def query_files(filepaths, filetype, log=warning, dir=None):
    """assess whether files in a dict are usable or not

    :param filepaths: dict to paths to files on disk
    :param filetype: string, used in logging messages
    :param log: logging function
    :param dir: path to a directory
    :return: dict of usable file paths and an integer indicating skipped files
    """

    result, skipped = dict(), 0
    for k, filepath in filepaths.items():
        fullpath = filepath
        if dir is not None:
            fullpath = join(dir, filepath)
        if query_file(fullpath, filetype, log):
            result[k] = fullpath
        else:
            skipped += 1
    return result, skipped


def require_file(filepath, filetype):
    """check if a file or directory exists, emit a message if not"""

    return query_file(filepath, filetype, log=error)

