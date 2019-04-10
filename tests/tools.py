'''Helper functions used within the test suite

@author: Tomasz Konopka
'''

from os import remove
from os.path import join, exists


def remove_file(files):
    """remove a single file if it exists."""

    for f in files:
        if exists(f):
            remove(f)


def remove_crossmap_cache(dir, name):
    """remove any crossmap cache files for a crossmap project"""


    prefix = join(dir, name+"-")
    remove_file([prefix + "target-features.tsv",
                 prefix + "target-ids.tsv",
                 prefix + "feature-map.tsv",
                 prefix + "document-features.tsv",
                 prefix + "items.tsv",
                 prefix + "data",
                 prefix + "ids",
                 prefix + "umap",
                 prefix + "embedding.tsv"])


def remove_featuremap_cache(dir, name):
    """remove any crossmap cache files for a crossmap project"""

    prefix = join(dir, name+"-")
    remove_file([prefix + "feature-map.tsv"])


