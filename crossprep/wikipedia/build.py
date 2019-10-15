"""
Build a dataset for crossmap from wikipedia articles.

Warning: This prorcedure performs very crude cleanup on wikipedia extracts.
The procedure tries to remove some html formatting, but the cleaning is
ad-hoc and incomplete. The attempt is to catch many of the common markups
and to produce output that is better than without any cleanup at all.
But the aim is not to produce a fully clean, or even html-valid, output.
"""

import gzip
import json
import re
import yaml
from logging import info, error, warning
from os.path import join, exists
from .download import wikipedia_pageids_file, wikipedia_exintros_file
from .download import read_pageids


# ad-hoc patterns to remove some html tags
html_patterns = ["<p>|</p>|<span>|</span>",
                 "<sup>|</sup>|<sub>|</sub>",
                 "<b>|</b>|<i>|</i>|<a>|</a>",
                 "<mi>|</mi>|<mo>|</mo>|<mn>|</mn>",
                 "<msup>|</msup>|<msub>|</msub>",
                 "<br>|<br/>|<semantics>|</semantics>",
                 "<math>|</math>|<mstyle>|</mstyle>|<mrow>|</mrow>",
                 "<annotation>|</annotation>"]
html_re = [re.compile(_) for _ in html_patterns]


def _rough_clean(t):
    """remove some html marking and whitespace"""

    result = t
    for compiled_pattern in html_re:
        result = compiled_pattern.sub("", result)
    result = re.sub("\n|\t", " ", result)
    result = re.sub("\s+", " ", result)
    return result.strip()


def _make_wikipedia_item(data, category):
    """create a dictionary with data, metadata"""

    id = "W:"+str(data["pageid"])
    result = dict(title=data["title"],
                  data=_rough_clean(data["extract"]),
                  metadata=dict(category=category))
    return id, result


def build_category_items(filepath, category):
    """read downloaded and build crossmap items"""

    result = dict()
    with gzip.open(filepath, "rt") as f:
        data = json.load(f)
    for d in data:
        id, content = _make_wikipedia_item(d, category)
        result[id] = content
    return result


def build_wikipedia_dataset(config):
    """assemble data from wikipedia articles into crossmap datasets"""

    category_name = " ".join(config.wikipedia_category)
    out_file = join(config.outdir, config.name + ".yaml.gz")
    if exists(out_file):
        info("output file already exists: " + out_file)
        return

    ids_file = wikipedia_pageids_file(config, category_name)
    if not exists(ids_file):
        error("file with page ids does not exist")
        return

    # load mapping from categories to page ids
    pages = read_pageids(ids_file)

    skip = set()
    exclude_pattern = config.wikipedia_exclude
    with gzip.open(out_file, "wt") as out:
        for category in pages.keys():
            if re.search(exclude_pattern, category):
                continue
            category_file = wikipedia_exintros_file(config, category)
            if not exists(category_file):
                warning("downloaded data does not exist: "+category)
                continue
            info("Processing: " + category)
            data = build_category_items(category_file, category)
            if len(data) == 0:
                continue
            # avoid adding same article through several categories
            for k in list(data.keys()):
                if k in skip:
                    data.pop(k)
            skip.update(data.keys())
            out.write(yaml.dump(data))

