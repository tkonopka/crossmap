"""Crossmap

Usage: python3 crossmap.py command

@author: Tomasz Konopka
"""


import argparse
import logging
from os import getcwd
from sys import exit
from crossmap.crossmap import Crossmap


parser = argparse.ArgumentParser(description="crossmap")

# utility
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["build", "tokens"])

# registering query and target objects
parser.add_argument("--config", action="store",
                    help="configuration file",
                    default=None)

# registering query and target objects
parser.add_argument("--source", action="store",
                    help="dataset with objects to map from")
parser.add_argument("--target", action="store",
                    help="dataset with objects to map onto")

# ############################################################################

logging.basicConfig(format='[%(asctime)s] %(levelname) -8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)


if __name__ == "__main__":
    config = parser.parse_args()

    crossmap = Crossmap(config.config)

    if not crossmap.valid():
        exit()

    if config.action == "tokens":
        # print out tokens in the source and target datasets
        crossmap.tokens()

    if config.action == "build":
        crossmap.build()
