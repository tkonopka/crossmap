"""
Collection of helper functions for pubmed.
"""

import logging
import gzip
import requests
from os.path import exists, basename
from os import makedirs
import xml.etree.ElementTree as XML


def ensure_dir(dirname):
    """Checks existence of a directory."""

    if not exists(dirname):
        makedirs(dirname)
    return dirname


def parse_indexes(x):
    """parse a string into a set of indexes"""

    # verify the quality of the input
    ok = [str(_) for _ in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, ",", "-"]]
    for d in x:
        if d not in ok:
            raise Exception("unacceptable index string")

    result = set()
    for xpart in x.split(","):
        xrange = xpart.split("-")
        if len(xrange) > 2:
            raise Exception("unacceptable index string")
        elif len(xrange)==1:
            result.add(int(xrange[0]))
        else:
            for _ in range(int(xrange[0]), int(xrange[1])+1):
                result.add(_)
    return sorted(list(result))


def download_one(url, filepath, skip_exists=True):
    """Carry out one file download

    Arguments:
        url         data source url
        filepath    destination file path
        skip_exists logical, whether to skip if local file already exists

    Returns:
        an integer code:  http status or 0 if file exists
    """

    if skip_exists and exists(filepath):
        logging.info("Exists: "+basename(filepath))
        return 0

    r = requests.get(url=url, stream=True)
    status = r.status_code
    if status != 200:
        if status == 404:
            logging.info("Does not exist: "+url)
        else:
            logging.info("Failed: "+url)
        r.close()
        return status
    logging.info("Downloading: "+basename(filepath))
    with open(filepath, "wb") as f:
        for chunk in r.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)
    r.close()
    return status


def load_xml(filepath):
    """read entire contents of an xml file and return an XML"""

    open_fn = open
    if filepath.endswith(".gz"):
        open_fn = gzip.open
    with open_fn(filepath, mode="r") as f:
        text = f.read().decode("utf-8")
    return XML.fromstring(text)

