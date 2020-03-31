"""
Helper functions used within the test suite
"""

import glob
from contextlib import suppress
from os import remove, rmdir
from os.path import join, exists
from pymongo import MongoClient


def remove_file(files):
    """remove a single file if it exists."""

    for f in files:
        if exists(f):
            remove(f)


def remove_crossmap_cache(dir, name, use_subdir=True):
    """remove any crossmap cache files for a crossmap project"""

    client = MongoClient(port=8097, username="root", password="rootpassword")
    client.drop_database(name)
    crossmap_data_dir = join(dir, name) if use_subdir else dir
    prefix = join(crossmap_data_dir, name)
    all_filenames = glob.glob(prefix+"*")
    remove_file(all_filenames)
    if exists(crossmap_data_dir):
        with suppress(OSError):
            rmdir(crossmap_data_dir)


def remove_cachefile(dir, filename):
    """remove a specific crossmap cache file"""

    filepath = join(dir, filename)
    remove_file([filepath])

