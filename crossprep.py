"""Crossprep

Command line interface to a suite of tools to prepare data for crossmap.

Usage: python3 crossprep.py command
"""


import argparse
import logging
from os import getcwd
from sys import exit
from crossprep.tools import save_dataset
from crossprep.obo.build import build_obo_dataset
from crossprep.orphanet.build import build_orphanet
from crossprep.pubmed.baseline import download_pubmed_baseline
from crossprep.pubmed.build import build_pubmed_dataset


# this is a command line utility
if __name__ != "__main__":
    exit()


# ############################################################################
# Arguments

parser = argparse.ArgumentParser(description="crossprep")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["obo", "orphanet", "pubmed", "baseline"])

# common arguments
parser.add_argument("--outdir", action="store",
                    help="Output directory",
                    default=getcwd())
parser.add_argument("--name", action="store",
                    help="name of output dataset",
                    default="")

# settings for obo
parser.add_argument("--obo", action="store",
                    help="path to obo file",
                    default=None)
parser.add_argument("--obo_root", action="store",
                    help="filtering by root node",
                    default=None)
parser.add_argument("--obo_aux", action="store",
                    help="types of auxiliary data to include, use P,N, or B",
                    default="")

# settings for orphanet
parser.add_argument("--orphanet", action="store",
                    help="path to orphanet disorder-phenotype xml")

# setting for pubmed baseline
parser.add_argument("--baseline_url", action="store",
                    help="PubMed URL to article baseline",
                    default="http://ftp.ncbi.nlm.nih.gov/pubmed/baseline/")
parser.add_argument("--baseline_template", action="store",
                    help="Template for filename with #s",
                    default="pubmed19n####.xml.gz")
parser.add_argument("--baseline_indexes", action="store",
                    help="Number of baseline data files to download",
                    default=None)
parser.add_argument("--baseline_sleep", action="store",
                    help="seconds to sleep between requests",
                    default=0.5)

# settings for pubmed build
parser.add_argument("--pubmed_pattern", action="store",
                    help="filtering by pattern",
                    default=None)
parser.add_argument("--pubmed_year", action="store",
                    help="filtering by publishing year",
                    default=None)
parser.add_argument("--pubmed_length", action="store",
                    help="filtering by minimum number of characters in primary data",
                    default=200)


# ############################################################################
# Script below assumes running from command line

config = parser.parse_args()

logging.basicConfig(format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.info("Starting "+config.action)

# set a nontrivial output file name
if config.name is None or config.name == "":
    config.name = config.action

if config.action == "obo":
    aux_pos = config.obo_aux in set(["P", "B"])
    aux_neg = config.obo_aux in set(["N", "B"])
    result = build_obo_dataset(config.obo, config.obo_root,
                               aux_pos=aux_pos, aux_neg=aux_neg)
    save_dataset(result, config.outdir, config.name)

elif config.action == "baseline":
    download_pubmed_baseline(config)

elif config.action == "pubmed":
    build_pubmed_dataset(config)

elif config.action == "orphanet":
    result = build_orphanet(config.orphanet)
    save_dataset(result, config.outdir, config.name)


logging.info("done")
