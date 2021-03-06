"""
Crossmap

Command line interface to crossmap document mapping.

Usage: python crossmap.py command
"""


import argparse
import logging
import sys
from os import environ, system
from os.path import join, dirname
from json import loads
from crossmap.settings import CrossmapSettings
from crossmap.crossmap import Crossmap, validate_dataset_label
from crossmap.crossmap import remove_db_and_files
from crossmap.info import CrossmapInfo
from crossmap.tools import concise_exception_handler, json_print, tsv_print

# this is a command line utility
if __name__ != "__main__":
    exit()
sys.excepthook = concise_exception_handler


# ############################################################################
# Arguments

parser = argparse.ArgumentParser(description="crossmap")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["build", "delete",
                             "search", "decompose",
                             "add", "remove",
                             "server", "gui",
                             "distances", "vectors", "matrix", "counts",
                             "diffuse", "features", "summary"])
parser.add_argument("--config", action="store",
                    help="configuration file",
                    default=None)
parser.add_argument("--data", action="store",
                    help="input dataset, list of objects")


# fine-tuning of predictions and output
parser.add_argument("--dataset", action="store",
                    default=None,
                    help="name of dataset to query, remove, etc.")
parser.add_argument("--n", action="store",
                    type=int, default=1,
                    help="number of targets")
parser.add_argument("--diffusion", action="store",
                    default=None,
                    help="JSON of a dict with diffusion strengths")
parser.add_argument("--factors", action="store",
                    default=None,
                    help="comma-separated ids for decomposition")
parser.add_argument("--pretty", action="store_true",
                    help="pretty-print JSON outputs for human readability")
parser.add_argument("--tsv", action="store_true",
                    help="output results in a table format")

# manual investigation/debugging
parser.add_argument("--ids", action="store",
                    help="comma-separated ids")
parser.add_argument("--text", action="store",
                    help="comma-separated text items")


# fine-tuning of logging
parser.add_argument("--logging", action="store",
                    default=None, choices=["WARNING", "INFO", "ERROR"],
                    help="logging levels, use WARNING, INFO, or ERROR")


# ############################################################################
# Script below assumes running from command line

config = parser.parse_args()
logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
if config.logging is not None:
    logging.getLogger().setLevel(config.logging)

if config.diffusion is not None:
    try:
        config.diffusion = loads(config.diffusion)
    except Exception as e:
        raise Exception("Error parsing diffusion json: "+str(e))
action = config.action

if config.logging is not None:
    logging.getLogger().setLevel(config.logging)

# output as json or tsv
output = tsv_print if config.tsv else json_print

# for build, settings check all data files are available
# for other actions, the settings can be lenient
settings = CrossmapSettings(config.config,
                            require_data_files=(action == "build"))
if not settings.valid:
    sys.exit()

crossmap = None
if action in {"search", "decompose"}:
    logging.getLogger().setLevel(level=logging.ERROR)
if action in {"build", "search", "decompose", "add", "remove"}:
    crossmap = Crossmap(settings)
if action in {"features", "diffuse", "distances", "matrix",
              "counts", "summary"}:
    crossmap = CrossmapInfo(settings)


# ############################################################################
# actions associated with primary functionality and batch processing

if action == "build":
    crossmap.build()
if action == "delete":
    remove_db_and_files(settings)

if action == "remove":
    crossmap.remove(config.dataset)

if action in {"search", "decompose"}:
    crossmap.load()
    config.dataset = validate_dataset_label(crossmap, config.dataset)
    if config.dataset is None:
        sys.exit()
    factors = None if config.factors is None else config.factors.split(",")
    if config.text is None:
        action_fun = crossmap.search_file
        if action == "decompose":
            action_fun = crossmap.decompose_file
        result = action_fun(config.data, config.dataset, n=config.n,
                            diffusion=config.diffusion, factors=factors)
    else:
        action_fun = crossmap.search
        if action == "decompose":
            action_fun = crossmap.decompose
        result = [action_fun(dict(data=config.text), config.dataset,
                             n=config.n, diffusion=config.diffusion,
                             factors=factors, query_name=config.text)]
    output(result, pretty=config.pretty)

if action == "add":
    crossmap.load()
    idxs = crossmap.add_file(config.dataset, config.data)


# ############################################################################
# actions associated with diagnostics

if action == "diffuse":
    result = []
    if config.data is not None:
        result.extend(crossmap.diffuse_file(config.data.split(","),
                                            diffusion=config.diffusion))
    if config.text is not None:
        result.extend(crossmap.diffuse_text(config.text.split(","),
                                            diffusion=config.diffusion))
    if config.ids is not None:
        result.extend(crossmap.diffuse_ids(config.dataset,
                                           config.ids.split(","),
                                           diffusion=config.diffusion))
    output(result, pretty=config.pretty)

if action in {"distances", "vectors", "matrix"}:
    crossmap = CrossmapInfo(settings)
    action_fun = crossmap.distance_file
    if action == "vectors":
        action_fun = crossmap.vectors
    elif action == "matrix":
        action_fun = crossmap.matrix
    result = action_fun(config.data, ids=config.ids.split(","),
                        diffusion=config.diffusion)
    output(result, pretty=config.pretty)

if action == "counts":
    config.dataset = validate_dataset_label(crossmap, config.dataset)
    result = crossmap.counts(config.dataset, features=config.ids.split(","))
    output(result, pretty=config.pretty)

if action in {"features", "summary"}:
    crossmap.load()
    action_fun = crossmap.summary
    if config.action == "features":
        action_fun = crossmap.features
    output(action_fun(), pretty=config.pretty)


# ############################################################################
# actions associated with the user interface

if action == "server":
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Could not import Django.")
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    environ.setdefault('DJANGO_CROSSMAP_CONFIG_PATH', config.config)
    ip_port = "0.0.0.0:"+str(settings.server.api_port)
    execute_from_command_line(['', 'runserver', ip_port])

if action == "gui":
    environ.setdefault('PORT', str(settings.server.ui_port))
    api_address = "0.0.0.0:"+str(settings.server.api_port)
    environ.setdefault('REACT_APP_API_URL', api_address)
    cmd = "npm start --prefix " + join(dirname(__file__), "crosschat")
    system(cmd)
