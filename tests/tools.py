"""
Helper functions used within the test suite
"""

from contextlib import suppress
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
    prefix = join(crossmap_data_dir, name)
    filenames = ["temp.tsv", "feature-map.tsv",
                 "targets-index", "targets-index.dat",
                 "documents-index", "documents-index.dat",
                 "manual-index", "manual-index.dat",
                 "pos.yaml", "pos-index", "pos-index.dat",
                 "neg.yaml", "neg-index", "neg-index.dat",
                 "targets-data", "documents-data", "manual.yaml"]
    filenames = [prefix + "-" + _ for _ in filenames]
    filenames.append(prefix + ".sqlite")
    remove_file(filenames)
    if exists(crossmap_data_dir):
        with suppress(OSError):
            rmdir(crossmap_data_dir)


def remove_cachefile(dir, filename):
    """remove a specific crossmap cache file"""

    filepath = join(dir, filename)
    remove_file([filepath])

