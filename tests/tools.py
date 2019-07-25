'''Helper functions used within the test suite
'''

from os import remove, rmdir
from os.path import join, exists


def remove_file(files):
    """remove a single file if it exists."""

    for f in files:
        if exists(f):
            remove(f)


def remove_crossmap_cache(dir, name, use_subdir=True):
    """remove any crossmap cache files for a crossmap project"""

    crossmap_data_dir = join(dir, name) if use_subdir else dir

    prefix = join(crossmap_data_dir, name+"-")
    remove_file([prefix + "target-features.tsv",
                 prefix + "target-ids.tsv",
                 prefix + "feature-map.tsv",
                 prefix + "document-features.tsv",
                 prefix + "items.tsv",
                 prefix + "data",
                 prefix + "ids",
                 prefix + "umap",
                 prefix + "embedding.tsv"])
    if exists(crossmap_data_dir):
        try:
            rmdir(crossmap_data_dir)
        except OSError:
            pass


def remove_featuremap_cache(dir, name):
    """remove any crossmap cache files for a crossmap project"""

    prefix = join(dir, name+"-")
    remove_file([prefix + "feature-map.tsv"])


