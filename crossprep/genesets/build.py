"""
Build a dataset based on genesets
"""

import gzip


def gmt(line):
    """parse a gmt line into id, name, gene symbols"""
    result = line[:-1].split("\t")
    return result[0], result[1], result[2:]


def build_gmt_dataset(filepath, min_size=0, max_size=100):
    """create a dict containing crossmap data for gene set
    :param data_path: character, path to table with a gene set tsv or gmt
    :param min_size: integer, minimal number of genes in set
    :param max_size: integer, maximal number of genes in set
    :return: dictionary with a crossmap dataset
    """

    open_fn = open
    if filepath.endswith(".gz"):
        open_fn = gzip.open

    result = dict()
    with open_fn(filepath, mode="rt") as f:
        for data in f:
            id, name, symbols = gmt(data)
            if len(symbols) < min_size or len(symbols) > max_size:
                continue
            result[id] = dict(title=name, data=name, aux_pos=symbols)
    return result

