"""Crossmap

Usage: python3 crossmap.py command

@author: Tomasz Konopka
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
parser.add_argument("--nn", action="store",
                    type=int, default=1,
                    help="number of nearest neighbors")
parser.add_argument("--pretty", action="store_true",
                    help="display prediction results using pretty-print")


# ############################################################################

logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)


if __name__ == "__main__":
    config = parser.parse_args()

    settings = CrossmapSettings(config.config)

    if not settings.valid:
        exit()

    crossmap = Crossmap(settings)

    if config.action == "build":
        crossmap.build()
        exit()

    if config.action == "predict":
        crossmap.load()
        result = crossmap.predict_file(config.data, n=config.nn)
        if config.pretty:
            result = dumps(result, indent=2)
        else:
            result = dumps(result)
        print(result)
