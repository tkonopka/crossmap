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
from json import dumps
from crossmap.settings import CrossmapSettings
from crossmap.crossmap import Crossmap


parser = argparse.ArgumentParser(description="crossmap")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["build", "predict", "decompose", "server", "ui", "distance"])
parser.add_argument("--config", action="store",
                    help="configuration file",
                    default=None)
parser.add_argument("--data", action="store",
                    help="dataset with objects to map from")


# fine-tuning of predictions and output
parser.add_argument("--n_targets", action="store",
                    type=int, default=1,
                    help="number of nearest targets")
parser.add_argument("--n_docs", action="store",
                    type=int, default=1,
                    help="number of documents used")
parser.add_argument("--report_docs", action="store_true",
                    help="include document ids in prediction output")
parser.add_argument("--pretty", action="store_true",
                    help="display prediction results using pretty-print")

# manual investigation/debugging
parser.add_argument("--ids", action="store",
                    help="comma-separate ids")


# fine-tuning of predictions and output
parser.add_argument("--logging", action="store",
                    default="WARNING", choices=["WARNING", "INFO", "ERROR"],
                    help="logging levels, use WARNING, INFO, or ERROR")


if __name__ != "__main__":
    sys.exit()


# ############################################################################
# Script below assumes running from command line

config = parser.parse_args()

logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.getLogger().setLevel(config.logging)


settings = CrossmapSettings(config.config)
if not settings.valid:
    sys.exit()


if config.action == "build":
    crossmap = Crossmap(settings)
    crossmap.build()
    sys.exit()

if config.action == "predict" or config.action == "decompose":
    logging.getLogger().setLevel(level=logging.ERROR)
    crossmap = Crossmap(settings)
    crossmap.load()
    action_fun = crossmap.predict_file
    if config.action == "decompose":
        action_fun = crossmap.decompose_file
    result = action_fun(config.data,
                        n_targets=config.n_targets, n_docs=config.n_docs,
                        options=config)
    if config.pretty:
        result = dumps(result, indent=2)
    else:
        result = dumps(result)
    print(result)
    sys.exit()

if config.action == "distance":
    crossmap = Crossmap(settings)
    crossmap.load()
    result = crossmap.distance_file(config.data, ids=config.ids.split(","))
    if config.pretty:
        result = dumps(result, indent=2)
    else:
        result = dumps(result)
    print(result)
    sys.exit()

if config.action == "server":
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Could not import Django.") from exc
    environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')
    environ.setdefault('DJANGO_CROSSMAP_CONFIG_PATH', settings.file)
    execute_from_command_line(['', 'runserver', str(settings.server.api_port)])
    sys.exit()

if config.action == "ui":
    environ.setdefault('PORT', str(settings.server.ui_port))
    cmd = "npm start --prefix " + join(dirname(__file__), "crosschat")
    system(cmd)
