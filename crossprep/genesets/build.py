"""
Build a dataset based on genesets
"""

import gzip
import sys
from yaml import dump


def gmt(line):
    """parse a gmt line into id, name, gene symbols"""
    result = line[:-1].split("\t")
    return result[0], result[1], result[2:]


def build_gmt_items(filepath, min_size=0, max_size=100):
    """generator of items for a crossmap dataset from a gmt file
    :param filepath: character, path to table with a gene set tsv or gmt
    :param min_size: integer, minimal number of genes in set
    :param max_size: integer, maximal number of genes in set
    :return: this is a generator
    """

    open_fn = gzip.open if filepath.endswith(".gz") else open
    with open_fn(filepath, mode="rt") as f:
        for data in f:
            item_id, name, symbols = gmt(data)
            if len(symbols) < min_size or len(symbols) > max_size:
                continue
            item = dict(title=name,
                        data={"name": name, "symbols": symbols},
                        metadata={"id": item_id, "length": len(symbols)})
            yield item_id, item


def build_gmt_dataset_dict(filepath, min_size=0, max_size=100):
    """create a dict containing crossmap data for gene set
    :param data_path: character, path to table with a gene set tsv or gmt
    :param min_size: integer, minimal number of genes in set
    :param max_size: integer, maximal number of genes in set
    :return: dictionary with a crossmap dataset
    """

    result = dict()
    for item_id, item in build_gmt_items(filepath, min_size, max_size):
        result[item_id] = item
    return result


def build_gmt_dataset(filepath, min_size=0, max_size=100, out=sys.stdout):
    """create a dataset by writing into a stream"""

    for item_id, item in build_gmt_items(filepath, min_size, max_size):
        out.write(dump({item_id: item}))
