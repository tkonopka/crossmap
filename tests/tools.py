"""
Helper functions used within the test suite
"""

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
    remove_file([prefix[:-1] + ".sqlite",
                 prefix + "temp.tsv",
                 prefix + "feature-map.tsv",
                 prefix + "index-targets.ann",
                 prefix + "index-documents.ann",
                 prefix + "targets-index",
                 prefix + "documents-index",
                 prefix + "targets-index.dat",
                 prefix + "documents-index.dat",
                 prefix + "targets-data",
                 prefix + "documents-data",
                 prefix + "documents-item-names",
                 prefix + "targets-item-names"])
    if exists(crossmap_data_dir):
        try:
            rmdir(crossmap_data_dir)
        except OSError:
            pass


def remove_cachefile(dir, filename):
    """remove a specific crossmap cache file"""

    filepath = join(dir, filename)
    remove_file([filepath])
