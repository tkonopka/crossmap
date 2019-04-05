"""Interface to using crossmap with pubmed data.

@author: Tomasz Konopka
"""


import argparse
import logging
from os import getcwd
from pubmed.baseline import download_baseline
from pubmed.build import build_pubmed_dataset


parser = argparse.ArgumentParser(description="crossprep-pubmed")
parser.add_argument("action", action="store",
                    help="name of utility",
                    choices=["download", "build"])

# inputs for utility: baseline
parser.add_argument("--url", action="store",
                    help="PubMed URL to article baseline",
                    default="http://ftp.ncbi.nlm.nih.gov/pubmed/baseline/")
parser.add_argument("--template", action="store",
                    help="Template for filename with #s",
                    default="pubmed19n####.xml.gz")
parser.add_argument("--indexes", action="store",
                    help="Number of baseline data files to download",
                    default=None)
parser.add_argument("--sleep", action="store",
                    help="seconds to sleep between requests",
                    default=0.5)

# inputs for utility: build
parser.add_argument("--pattern", action="store",
                    help="filtering by pattern",
                    default=None)
parser.add_argument("--year", action="store",
                    help="filtering by publishing year",
                    default=None)
parser.add_argument("--length", action="store",
                    help="filtering by minimum number of characters in primary data",
                    default=200)
parser.add_argument("--name", action="store",
                    help="name of output dataset",
                    default="pubmed")

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
    
    if config.action == "download":
        download_baseline(config)
    if config.action == "build":
        build_pubmed_dataset(config)

    logging.info("Done")
