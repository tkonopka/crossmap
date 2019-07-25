"""Interface to using crossmap with ontologies.
"""

import argparse
import gzip
import logging
import yaml
from os import getcwd
from os.path import join
from obo.build import build_obo_dataset


parser = argparse.ArgumentParser(description="crossprep-obo")
parser.add_argument("action", action="store",
                    help="name of utility",
                    choices=["build"])

# inputs for utility: build
parser.add_argument("--obo", action="store", required=True,
                    help="path to obo file",
                    default=None)
parser.add_argument("--name", action="store", required=True,
                    help="name of output dataset",
                    default="obo")
parser.add_argument("--root", action="store",
                    help="filtering by root node",
                    default=None)

# outputs
parser.add_argument("--outdir", action="store", required=True,
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
        result = build_obo_dataset(config.obo, config.root)
        out_file = join(config.outdir, config.name+".yaml.gz")
        with gzip.open(out_file, "wt") as out:
            out.write(yaml.dump(result))

    logging.info("Done")
