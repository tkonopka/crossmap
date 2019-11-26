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


def parse_def(definition_text):
    """create a short string from a long wikitionary definition field"""

    if definition_text is None:
        return ""

    # sections that contribute bulk content
    hit_sections = {"===Noun===", "===Verb===", "===Adjective==="}
    # section that contain links (to be copied)
    link_sections = {"===Related terms===", "====Related terms===="}

    result = []
    hit_section = False
    link_section = False
    language = False
    for line in definition_text.split("\n"):
        # assess/update the location of the line in the document
        if line.startswith("="):
            level = header_level(line)
            if level == 2:
                language = (line == "==English==")
            if level == 3 or level == 4:
                hit_section = (line in hit_sections)
                link_section = (line in link_sections)
        # decide whether to transfer the line into the result
        if hit_section and language and line.startswith("# "):
            data = line[2:].replace("[[", "").replace("]]", "")
            data = double_curly.sub("", data)
            result.append(data.strip())
        if link_section and language and line.startswith("* "):
            data = line[2:].replace("}}", "")
            data = curly_pipe.sub("", data)
            result.append(data.strip())

    # clean up some common artifacts
    result = (" ".join(result))
    for x in ref:
        result = x.sub("", result)
    result = quotes.sub("'", result)
    return result.replace("  ", " ").strip()


def build_wiktionary_item(page_text):
    """create an id and a crossmap item from an xml string"""

    id, data = None, dict()
    root = ET.fromstring(page_text.strip())
    for child in root:
        if child.tag == "title":
            data["title"] = child.text
            data["data"] = child.text
        elif child.tag == "id":
            id = child.text
        elif child.tag == "revision":
            for subchild in child:
                if subchild.tag == "text":
                    data["aux_pos"] = parse_def(subchild.text)
    return "WIKTIONARY:"+str(id), data


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
            id, data = build_wiktionary_item(page_str)
            title = data["title"]
            if data["aux_pos"] == "":
                continue
            if title == title.upper():
                continue
            if len(data["aux_pos"]) < len_ratio * len(data["data"]):
                continue
            item = dict()
            item[id] = data
            f.write(yaml.dump(item))

