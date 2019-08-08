"""Crossmap

Command line interface to crossmap document mapping.

Usage: python3 crossmap.py command
"""


import argparse
import logging
from json import dumps
from sys import exit
from crossmap.settings import CrossmapSettings
from crossmap.crossmap import Crossmap


parser = argparse.ArgumentParser(description="crossmap")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["build", "predict"])
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
parser.add_argument("--pretty", action="store_true",
                    help="display prediction results using pretty-print")

# fine-tuning of predictions and output
parser.add_argument("--logging", action="store",
                    default="WARNING",
                    help="logging levels, use WARNING, INFO, or ERROR")


if __name__ != "__main__":
    exit()


# ############################################################################
# Script below assumes running from command line

config = parser.parse_args()

logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.getLogger().setLevel(config.logging)


settings = CrossmapSettings(config.config)
if not settings.valid:
    exit()

crossmap = Crossmap(settings)

if config.action == "build":
    crossmap.build()
    exit()

if config.action == "predict":
    logging.getLogger().setLevel(level=logging.ERROR)
    crossmap.load()
    result = crossmap.predict_file(config.data,
                                   n=config.n_targets,
                                   n_docs=config.n_docs)
    if config.pretty:
        result = dumps(result, indent=2)
    else:
        result = dumps(result)
    print(result)
