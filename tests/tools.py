'''Helper functions used within the test suite

@author: Tomasz Konopka
'''

from os import remove
from os.path import join, exists


def remove_file(f):
    """remove a single file if it exists."""

    if exists(f):
        remove(f)


def remove_crossmap_cache(dir, name):
    """remove any crossmap cache files for a crossmap project"""

    prefix = join(dir, name+"-")
    remove_file(prefix + "target-tokens.txt")
