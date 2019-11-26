"""
Crossmap

Command line interface to crossmap document mapping.

Usage: python3 crossmap.py command
"""


import argparse
import logging
import sys
from os import environ, system
from os.path import join, dirname
from json import dumps, loads
from crossmap.settings import CrossmapSettings
from crossmap.crossmap import Crossmap, validate_dataset_label
from crossmap.info import CrossmapInfo


parser = argparse.ArgumentParser(description="crossmap")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["build", "search", "decompose", "add",
                             "server", "ui",
                             "distances", "vectors", "counts", "diffuse",
                             "features", "summary"])
parser.add_argument("--config", action="store",
                    help="configuration file",
                    default=None)
parser.add_argument("--data", action="store",
                    help="dataset with objects to map from")


# fine-tuning of predictions and output
parser.add_argument("--dataset", action="store",
                    default=None,
                    help="name of dataset")
parser.add_argument("--n", action="store",
                    type=int, default=1,
                    help="number of targets")
parser.add_argument("--paths", action="store",
                    default=None,
                    help="JSON of a dict with numbers of indirect paths")
parser.add_argument("--diffusion", action="store",
                    default=None,
                    help="JSON of a dict setting diffusion strengths")
parser.add_argument("--pretty", action="store_true",
                    help="display prediction results using pretty-print")

# manual investigation/debugging
parser.add_argument("--ids", action="store",
                    help="comma-separate ids")


# fine-tuning of predictions and output
parser.add_argument("--logging", action="store",
                    default=None, choices=["WARNING", "INFO", "ERROR"],
                    help="logging levels, use WARNING, INFO, or ERROR")


if __name__ != "__main__":
    sys.exit()


# ############################################################################
# Script below assumes running from command line


config = parser.parse_args()
if config.paths is not None:
    config.paths = loads(config.paths)
if config.diffusion is not None:
    config.diffusion = loads(config.diffusion)
action = config.action

logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
if config.logging is not None:
    logging.getLogger().setLevel(config.logging)


settings = CrossmapSettings(config.config)
if config.logging is not None:
    logging.getLogger().setLevel(config.logging)
if not settings.valid:
    sys.exit()


def print_exit(x, pretty=False):
    """helper to print something and terminate"""
    if pretty:
        x = dumps(x, indent=2)
    else:
        x = dumps(x)
    print(x)
    sys.exit()


# ############################################################################
# actions associated with primary functionality and batch processing

if action == "build":
    crossmap = Crossmap(settings)
    crossmap.build()
    sys.exit()

if action in set(["search", "decompose"]):
    logging.getLogger().setLevel(level=logging.ERROR)
    crossmap = Crossmap(settings)
    crossmap.load()
    config.dataset = validate_dataset_label(crossmap, config.dataset)
    if config.dataset is None:
        sys.exit()
    action_fun = crossmap.search_file
    if action == "decompose":
        action_fun = crossmap.decompose_file
    result = action_fun(config.data, config.dataset,
                        n=config.n, paths=config.paths,
                        diffusion=config.diffusion)
    print_exit(result, config.pretty)

if action == "add":
    crossmap = Crossmap(settings)
    crossmap.load()
    idxs = crossmap.add_file(config.dataset, config.data)
    print_exit(idxs, config.pretty)


# ############################################################################
# actions associated with diagnostics

if action == "diffuse":
    crossmap = CrossmapInfo(settings)
    result = crossmap.diffuse_ids(config.ids.split(","), diffusion=config.diffusion)
    print_exit(result, config.pretty)

if action in set(["distances", "vectors"]):
    crossmap = CrossmapInfo(settings)
    action_fun = crossmap.distance_file
    if action == "vectors":
        action_fun = crossmap.vectors
    result = action_fun(config.data, ids=config.ids.split(","),
                        diffusion=config.diffusion)
    print_exit(result, config.pretty)

if action == "counts":
    crossmap = CrossmapInfo(settings)
    config.dataset = validate_dataset_label(crossmap, config.dataset)
    result = crossmap.counts(config.dataset, features=config.ids.split(","))
    print_exit(result, config.pretty)

if action in set(["features", "summary"]):
    crossmap = Crossmap(settings)
    crossmap.load()
    action_fun = crossmap.summary
    if config.action == "features":
        action_fun = crossmap.features
    print_exit(action_fun(), config.pretty)


# ############################################################################
# actions associated with the user interface

if action == "server":
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Could not import Django.") from exc
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    environ.setdefault('DJANGO_CROSSMAP_CONFIG_PATH', settings.file)
    execute_from_command_line(['', 'runserver', str(settings.server.api_port)])
    sys.exit()

if action == "ui":
    environ.setdefault('PORT', str(settings.server.ui_port))
    cmd = "npm start --prefix " + join(dirname(__file__), "crosschat")
    system(cmd)
