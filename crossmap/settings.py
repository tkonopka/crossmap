"""
Crossmap settings and validation
"""

import yaml
from logging import error, warning
from os import getcwd, mkdir
from os.path import join, exists, dirname, basename, isdir
from .tokens import Kmerizer

# a tokenizer with default parameters
default_tokenizer = Kmerizer()


# ############################################################################
# Classes for settings, organized into groups by topic


class CrossmapKmerSettings():
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
        result = "Crossmap Kmer Settings:\n"
        result += "k=" + str(self.k) + ", "
        result += "alphabet='" + str(self.alphabet) + "'"
        return result


class CrossmapFeatureSettings:
    """Container for settings related to features"""

    def __init__(self, config=None):
        self.max_number = 0
        self.weighting = [1, 0]
        self.aux_weight = (0.5, 0.5)

        if config is None:
            return
        for key, val in config.items():
            if key == "max_number":
                self.max_number = int(val)
            elif key == "weighting":
                self.weighting = [float(_) for _ in val]
            elif key == "aux_weight":
                self.aux_weight = [float(_) for _ in val]

    def __str__(self):
        result = "Crossmap Feature Settings:\n"
        result += "max_number=" + str(self.max_number) + ", "
        result += "weighting='" + str(self.weighting) + "', "
        result += "aux_weight=" + str(self.aux_weight)
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


# ############################################################################
# Classes for setting groups

class CrossmapSettingsDefaults:
    """Container defining all settings for a crossmap project"""

    def __init__(self):
        self.name = ""
        self.dir = getcwd()
        self.prefix = join(self.dir, self.name)
        self.file = "crossmap.yaml"
        # paths to disk files
        self.data_files = dict()
        self.feature_map_file = None
        # settings for features (e.g. number of features)
        self.features = CrossmapFeatureSettings()
        # settings for tokens (e.g. kmer length)
        self.tokens = CrossmapKmerSettings()
        # settings for server (e.g. port)
        self.server = CrossmapServerSettings()
        # summary of state
        self.valid = False

    def db_file(self):
        """create path to db file"""
        return join(self.prefix, self.name + ".sqlite")

    def tsv_file(self, label):
        """create a file path for project tsv data"""
        return join(self.prefix, self.name + "-" + label + ".tsv")

    def pickle_file(self, label):
        """create a file path for project binary data object"""
        return join(self.prefix, self.name + "-" + label)

    def index_file(self, label):
        """create a file path for a project index file"""
        return join(self.prefix, self.name + "-" + label + "-index")


class CrossmapSettings(CrossmapSettingsDefaults):
    """Container keeping and validating settings for a Crossmap project"""

    def __init__(self, config, create_dir=False):
        """create a settings object

        :param config: path to a configuration file
        :param create_dir: logical, create directory automatically
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
            elif k == "feature_map":
                self.feature_map_file = v
            elif k == "tokens":
                self.tokens = CrossmapKmerSettings(v)
            elif k == "features":
                self.features = CrossmapFeatureSettings(v)
            elif k == "server":
                self.server = CrossmapServerSettings(v)
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

        # target objects to map toward
        self.data_files, skipped = query_files(self.data_files, "data file", dir=dir)
        result["data"] = len(self.data_files) > 0
        if not result["data"]:
            error(missing_msg + "'data'")

        if self.feature_map_file is not None:
            self.feature_map_file = join(dir, self.feature_map_file)
        result["feature_map"] = query_file(self.feature_map_file, "feature_map")

        result["weighting"] = True
        if len(self.features.weighting) != 2:
            self.features.weighting = [1, 0]
            warning(incorrect_msg + 'weighting')

        return result

    def files_deprecated(self, file_types):
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
            if file_type not in set(["targets", "documents", "featuremap"]):
                ft = str(file_type)
                warning("attempting to retrieve unknown file type: " + ft)
                continue
            for _ in self.__dict__[file_type]:
                result.append(join(self.dir, _))
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

