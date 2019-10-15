"""
Download information data for a Wikipedia category

This script is modified starting from a minimal example on mediawiki.org
https://www.mediawiki.org/wiki/API:Categorymembers
(original: MIT license)
"""


import csv
import time
import gzip
import requests
import json
import re
from logging import error, info
from os.path import join, exists
from os import makedirs


# settings to contact Wikipedia
api_url = "https://en.wikipedia.org/w/api.php"
categorymembers_params = {
    "action": "query",
    "cmlimit": "400",
    "list": "categorymembers",
    "format": "json"
}
exintros_params = {
    "action": "query",
    "prop": "extracts",
    "exintro": "true",
    "exlimit": "20",
    "format": "json"
}


def ensure_dir(dirname):
    """Checks existence of a directory."""

    if not exists(dirname):
        makedirs(dirname)
    return dirname


def _make_page_data(pageid, title, type, parent):
    """organize a bunch of field into a dictionary"""
    return dict(pageid=pageid, title=title,
                type=type, parent=parent)


pageid_columns = ["pageid", "title", "type", "parent"]


def _make_page_str(data):
    if data is None:
        return "\t".join(pageid_columns) + "\n"
    temp = [str(data[_]) for _ in pageid_columns]
    return "\t".join(temp) + "\n"


def _download_category_list(category, sleep_interval):
    """recursively download listing of a category and all subcategories"""

    info("downloading category listing: "+category)
    S = requests.Session()
    params = categorymembers_params.copy()
    params["cmtitle"] = "Category:" + category

    done = False
    result, subcategories = [], []
    while not done:
        api_result = S.get(url=api_url, params=params).json()
        if "query" in api_result:
            for x in api_result["query"]["categorymembers"]:
                x_title = x["title"]
                x_id = x["pageid"]
                x_type = "Article"
                if x_title.startswith("Category:"):
                    x_title = x_title[9:]
                    subcategories.append(x_title)
                    x_type = "Category"
                x_data = _make_page_data(x_id, x_title, x_type, category)
                result.append(x_data)
        done = "continue" not in api_result
        if not done:
            params["cmcontinue"] = api_result["continue"]["cmcontinue"]

    # process subcategories
    time.sleep(sleep_interval)
    for subcat in subcategories:
        result.extend(_download_category_list(subcat, sleep_interval))

    return result


def _download_exintros(pageids, sleep_interval, category):
    """carry out fetch requests for exintros"""

    info("downloading exintros: " + category)
    S = requests.Session()
    params = exintros_params.copy()
    params["pageids"] = "|".join(pageids)

    result = []
    for i in range(0, len(pageids), 16):
        params["pageids"] = "|".join(pageids[i:min(i+16, len(pageids))])
        api_result = S.get(url=api_url, params=params).json()
        if "query" in api_result:
            for _, extract in api_result["query"]["pages"].items():
                result.append(extract)

    time.sleep(sleep_interval)
    return result


def wikipedia_pageids_file(config, category):
    """generate a file path to a file with a table of pageids"""

    out_dir = join(config.outdir, "wikipedia_data")
    ensure_dir(out_dir)
    category = category.replace(" ", "_")
    return join(out_dir, "wikipedia.pageids." + category + ".txt.gz")


def wikipedia_exintros_file(config, category):
    """generate a file path to a file with a table of pageids"""

    out_dir = join(config.outdir, "wikipedia_data")
    ensure_dir(out_dir)
    category = category.replace(" ", "_")
    return join(out_dir, "wikipedia." + category + ".json.gz")


def read_pageids(ids_file):
    """read a csv file into a mapping between categories and pages"""

    result = dict()
    with gzip.open(ids_file, "rt") as f:
        reader = csv.DictReader(f, delimiter="\t", quotechar="\"")
        for row in reader:
            parent = row["parent"]
            if parent not in result:
                result[parent] = []
            if row["type"] == "Article":
                result[parent].append(row["pageid"])
    return result


def download_wikipedia_pageids(config, out_file):
    """download and save a summary of all wikipedia pages in a category

    :param config: argparse object.
        Must have config.wikipedia_category and config.wikipedia_sleep
    :param out_file: string, file to save page ids into
    """

    category = config.wikipedia_category
    if type(category) is not str:
        category = " ".join(category)
    result = _download_category_list(category, config.wikipedia_sleep)

    with gzip.open(out_file, "wt") as out:
        out.write(_make_page_str(None))
        for x in result:
            out.write(_make_page_str(x))


def download_wikipedia_exintros(config):
    """download exintros for all articles pertaining to a root category

    The download will exclude categories that match config.wikipedia_exclude
    """

    category_name = " ".join(config.wikipedia_category)
    if category_name is None or category_name == "":
        error("missing category name")
        return

    pageids_file = wikipedia_pageids_file(config, category_name)
    if not exists(pageids_file):
        download_wikipedia_pageids(config, pageids_file)

    # load mapping from categories to page ids
    pages = read_pageids(pageids_file)

    # download page content for each of the categories
    exclude_pattern = config.wikipedia_exclude
    for category in pages.keys():
        if re.search(exclude_pattern, category):
            continue
        category_file = wikipedia_exintros_file(config, category)
        if exists(category_file):
            continue
        exintros = _download_exintros(pages[category],
                                      config.wikipedia_sleep, category)
        with gzip.open(category_file, "wt") as f:
            f.write(json.dumps(exintros, indent=2))

