"""
Crossprep

Command line interface to a suite of tools to prepare data for crossmap.

Usage: python crossprep.py command
"""

import argparse
import gzip
import logging
import sys
from os import getcwd
from os.path import join
from crossmap.tools import concise_exception_handler
from crossprep.tools import save_dataset
from crossprep.obo.build import build_obo_dataset
from crossprep.opentargets.build import build_opentargets_dataset
from crossprep.orphanet.build import build_orphanet_dataset
from crossprep.pubmed.baseline import download_pubmed_baseline
from crossprep.pubmed.build import build_pubmed_dataset
from crossprep.genesets.build import build_gmt_dataset
from crossprep.wikipedia.download import download_wikipedia_exintros
from crossprep.wikipedia.build import build_wikipedia_dataset
from crossprep.wiktionary.build import build_wiktionary_dataset

# this is a command line utility
if __name__ != "__main__":
    sys.exit()

sys.excepthook = concise_exception_handler


# ############################################################################
# Arguments

parser = argparse.ArgumentParser(description="crossprep")
parser.add_argument("action", action="store",
                    help="Name of utility",
                    choices=["obo", "opentargets", "orphanet", "pubmed",
                             "pubmed_baseline", "genesets", "wikipedia",
                             "wiktionary"])

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
                    help="types of auxiliary data to include",
                    default="parents,comments")

# settings for opentargets
parser.add_argument("--opentargets_associations", action="store",
                    help="path to associations file",
                    default=None)
parser.add_argument("--opentargets_disease", action="store",
                    help="prefix for disease ids",
                    default=None)

# settings for orphanet
parser.add_argument("--orphanet_phenotypes", action="store",
                    help="path to orphanet disorder-phenotype xml")
parser.add_argument("--orphanet_genes", action="store",
                    help="path to orphanet disorder-gene xml")
parser.add_argument("--orphanet_nomenclature", action="store",
                    help="path to orphanet disorder-nomenclature xml")

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

# settings for geneset build
parser.add_argument("--gmt", action="store",
                    help="path to gmt file with genesets",
                    default=None)
parser.add_argument("--gmt_min_size", action="store", type=int,
                    help="minimal number of genes in a gmt gene set",
                    default=5)
parser.add_argument("--gmt_max_size", action="store", type=int,
                    help="maximal number of genes in a gmt gene set",
                    default=100)

# settings for wikipedia build
parser.add_argument("--wikipedia_category", action="store", type=str, nargs="+",
                    help="name of wikipedia category",
                    default=None)
parser.add_argument("--wikipedia_exclude", action="store", type=str,
                    help="patterns of categories to exclude",
                    default="^List|by\scountry")
parser.add_argument("--wikipedia_sleep", action="store",
                    help="seconds to sleep between requests",
                    default=0.1)

# settings for wiktionary build
parser.add_argument("--wiktionary", action="store", type=str,
                    help="path to wiktionary xml",
                    default=None)
parser.add_argument("--wiktionary_length", action="store", type=float,
                    help="minimal ratio of definition to word",
                    default=6)


# ############################################################################
# Script below assumes running from command line

config = parser.parse_args()

logging.basicConfig(format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)
logging.info("Starting " + config.action + " - " + str(config.name) )


def missing_arguments(argnames):
    """determine if arguments required for an action are missing

    :param argnames: list of argument names to check in object "config"
    :return: True if any of the arguments are set to None
    """
    missing = set()
    for argname in argnames:
        if getattr(config, argname) is None:
            missing.add(argname)
    if len(missing) > 0:
        logging.error("missing required arguments: " + ", ".join(missing))
    return len(missing) > 0


# set a nontrivial output file name
if config.name is None or config.name == "":
    config.name = config.action

result = None
result_file = join(config.outdir, config.name + ".yaml.gz")


if config.action == "obo":
    if missing_arguments(["obo"]):
        sys.exit()
    with gzip.open(result_file, "wt") as f:
        build_obo_dataset(config.obo, config.obo_root,
                          aux=config.obo_aux, out=f)

elif config.action == "pubmed_baseline":
    download_pubmed_baseline(config)

elif config.action == "pubmed":
    build_pubmed_dataset(config)

elif config.action == "wikipedia":
    download_wikipedia_exintros(config)
    build_wikipedia_dataset(config)

elif config.action == "wiktionary":
    build_wiktionary_dataset(config)

elif config.action == "opentargets":
    gene_file = join(config.outdir, config.name + "-genes.yaml.gz")
    disease_file = join(config.outdir, config.name + "-diseases.yaml.gz")
    # this processing is in two passes
    # this is somewhat wasteful but makes  implementation simpler
    with gzip.open(gene_file, "wt") as f:
        build_opentargets_dataset(config.opentargets_associations,
                                  config.opentargets_disease,
                                  "gene", out=f)
    with gzip.open(disease_file, "wt") as f:
        build_opentargets_dataset(config.opentargets_associations,
                                  config.opentargets_disease,
                                  "disease", out=f)

elif config.action == "orphanet":
    orphanet_fields = ["orphanet_phenotypes", "orphanet_genes",
                       "orphanet_nomenclature"]
    if missing_arguments(orphanet_fields):
        sys.exit()
    result = build_orphanet_dataset(config.orphanet_phenotypes,
                                    config.orphanet_genes,
                                    config.orphanet_nomenclature)

elif config.action == "genesets":
    if missing_arguments(["gmt"]):
        sys.exit()
    with gzip.open(result_file, "wt") as f:
        build_gmt_dataset(config.gmt,
                          config.gmt_min_size, config.gmt_max_size,
                          out=f)


if result is not None:
    save_dataset(result, config.outdir, config.name)

logging.info("done")
