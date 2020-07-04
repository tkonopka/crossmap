"""
Build a crossmap dataset from a wiktionary bulk download
"""

import gzip
import bz2
import re
import yaml
import xml.etree.ElementTree as ET
from logging import error, info
from os.path import join, exists


def wiktionary_page(wiktionary_path):
    """a generator of string for <page> items in the wiktionary"""

    page = []
    header = True
    with bz2.open(wiktionary_path, "rt") as f:
        for line in f:
            if line.strip() == "<page>":
                header = False
            if not header:
                page.append(line)
            if line.strip() == "</page>":
                yield "".join(page)
                page = []


def header_level(s):
    """count the number of equal signs at beginning of a string"""

    result = 0
    for letter in s:
        if letter == "=":
            result += 1
        else:
            break
    return result


# a special regex pattern to detect codes such as {{ab|cd|xyz}}
double_curly = re.compile("{{[^}]+}}")
ref = [re.compile("<ref[^>]*>"), re.compile("</ref>"),
       re.compile("<!--.*-->")]
quotes = re.compile("'+")
# a special regex pattern to detect the inside of curly {{ab|cd|text
curly_pipe = re.compile("{{.+\|")


def clean_def(s):
    """clean a string using global regular experssions"""

    result = s
    for x in ref:
        result = x.sub("", result)
    result = quotes.sub("'", result)
    return result.replace("  ", " ").strip()


def parse_def(definition_text):
    """create short strings from a long wikitionary definition field"""

    # sections that contribute bulk content
    hit_sections = {"===Noun===", "===Verb===", "===Adjective===",
                    "====Noun====", "====Verb====", "====Adjective===="}
    # section that contain links (to be copied)
    link_sections = {"===Related terms===", "====Related terms===="}

    result = dict(noun=[], verb=[], adjective=[], related=[])
    language, hit_section, link_section = False, False, False
    hit_type = ""
    for line in definition_text.split("\n"):
        # assess/update the location of the line in the document
        if line.startswith("="):
            level = header_level(line)
            if level == 2:
                language = (line == "==English==")
            if level == 3 or level == 4:
                hit_section = (line in hit_sections)
                if hit_section:
                    hit_type = line.replace("=", "").lower()
                link_section = (line in link_sections)
                if link_section:
                    hit_type = "related"
        # decide whether to transfer the line into the result
        if hit_section and language and line.startswith("# "):
            data = line[2:].replace("[[", "").replace("]]", "")
            data = double_curly.sub("", data)
            data = clean_def(data.strip())
            if len(data) > 1:
                result[hit_type].append(data)
        if link_section and language and line.startswith("* "):
            data = line[2:].replace("}}", "")
            data = curly_pipe.sub("", data)
            data = clean_def(data.strip())
            if len(data) > 1:
                result[hit_type].append(data)

    return result


def merge_dicts(a, b):
    """combine two dictionaries, assuming components are arrays"""

    result = a
    for k, v in b.items():
        if k not in result:
            result[k] = []
        result[k].extend(v)
    return result


def build_wiktionary_item(page_text, config):
    """create an id and a crossmap item from an xml string"""

    min_raw = config.wiktionary_minraw
    id, term, definitions = "", "", dict()
    root = ET.fromstring(page_text.strip())
    for child in root:
        if child.tag == "title":
            term = child.text
        elif child.tag == "id":
            id = child.text
        elif child.tag == "revision":
            for subchild in child:
                if subchild.tag == "text":
                    if subchild.text is None:
                        continue
                    if len(subchild.text) < min_raw:
                        continue
                    definitions = merge_dicts(definitions,
                                              parse_def(subchild.text))
    definitions["term"] = term
    for k in list(definitions.keys()):
        if len(definitions[k]) == 0:
           definitions.pop(k)
    return "WIKTIONARY:"+str(id), dict(title=term, data=definitions)


def build_wiktionary_dataset(config):
    """parses a wiktionary xml and produces a crossmap dataset

    :param config: argparse configuration with elements .wiktionary
    """

    wiktionary_file = config.wiktionary
    if wiktionary_file is None or not exists(wiktionary_file):
        error("Wiktionary file does not exist: " + str(wiktionary_file))
        return

    out_file = join(config.outdir, config.name + ".yaml.gz")
    if exists(out_file):
        info("output file already exists: "+out_file)
        return

    len_ratio = config.wiktionary_length
    with gzip.open(out_file, "wt") as f:
        for page_str in wiktionary_page(wiktionary_file):
            id, data = build_wiktionary_item(page_str, config)
            definitions = data["data"]
            if len(definitions) <= 1:
                continue
            definition = str(definitions)
            title = data["title"]
            if title == title.upper():
                continue
            if len(definition) < len_ratio * len(title):
                continue
            if config.wiktionary_singles and len(title.split(" ")) > 1:
                continue
            item = dict()
            if config.wiktionary_separate:
                definitions.pop("term")
                for k, v in definitions.items():
                    item_k = dict(title=title, data={"term": title, k: v})
                    item[id + "." + k] = item_k
            else:
                item[id] = data
            f.write(yaml.dump(item))

