"""Preparing orphanet data for use with crossmap
"""


import argparse
import logging
from os import getcwd
from orphanet.build import build_orphanet_dataset


parser = argparse.ArgumentParser(description="crossprep-orphanet")
parser.add_argument("action", action="store",
                    help="name of utility",
                    choices=["build"])

parser.add_argument("--input", action="store", required=True,
                    help="path to input dataset")
parser.add_argument("--name", action="store",
                    help="name of output dataset",
                    default="orphanet")

# outputs
parser.add_argument("--outdir", action="store",
                    help="Output directory",
                    default=getcwd())


# ############################################################################

logging.basicConfig(format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

if __name__ == "__main__":
    
    config = parser.parse_args()

    logging.info("Starting "+config.action)
    
    if config.action == "build":
        build_orphanet_dataset(config)

    logging.info("Done")
