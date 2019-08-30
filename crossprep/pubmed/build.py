"""
Build a dataset for crossmap from pubmed baseline data files.
"""

import gzip
import logging
import yaml
import re
from os import listdir
from os.path import join
from .tools import ensure_dir, load_xml, parse_indexes


class Article():
    """Container for article metadata."""

    def __init__(self, medlinenode):
        """Create a new article container, parse
        data from a medline xml node."""

        self.pmid = 0
        self.title = ""
        self.journal = ""
        self.year = ""
        self.keywords = []
        self.abstract = ""
        self.valid = True

        for c in medlinenode.getchildren():
            if c.tag == "PMID":
                self._parse_pmid(c)
            elif c.tag == "Article":
                self._parse_article(c)
            elif c.tag == "MeshHeadingList":
                self._parse_mesh(c)

        if self.title is None or self.abstract is None or self.year is None:
            self.valid = False

    def _parse_pmid(self, xmlnode):
        """Parse metadata from a <PMID> node."""

        self.pmid = int(xmlnode.text)

    def _parse_journal(self, xmlnode):
        """Parse metadata from a <Journal> node."""

        for c in xmlnode.getchildren():
            if c.tag == "JournalIssue":
                for c2 in c.getchildren():
                    if c2.tag == "PubDate":
                        for c3 in c2.getchildren():
                            if c3.tag == "MedlineDate" or c3.tag == "Year":
                                year = re.split(" |-", c3.text)[0]
                                try:
                                    year = int(year)
                                except ValueError:
                                    pass
                                self.year = year
            elif c.tag == "Title":
                self.journal = c.text

    def _parse_abstract(self, xmlnode):
        """Parse metadata from a <Abstract> node."""

        for c in xmlnode.getchildren():
            if c.tag == "AbstractText":
                if self.abstract != "":
                    self.abstract += " "
                if c.text is not None:
                    self.abstract += c.text

    def _parse_article(self, xmlnode):
        """Parse metadata from an <Article> node."""

        for c in xmlnode.getchildren():
            if c.tag == "Journal":
                self._parse_journal(c)
            elif c.tag == "ArticleTitle":
                self.title = c.text
            elif c.tag == "Abstract":
                self._parse_abstract(c)

    def _parse_mesh(self, xmlnode):
        """Parse metadata from a <MeshHeadingList>"""

        for c in xmlnode.getchildren():
            for c2 in c.getchildren():
                if c2.tag == "DescriptorName":
                    self.keywords.append(c2.text)


def build_pubmed_one(config, xmlnode):
    """Transfer data for one article into a dict

    Arguments:
        config    dictionary with settings
        xmlnode   XML node, expected like <MedlineCitation>

    Returns:
        pmid and a dictionary with content for one article
    """

    article = Article(xmlnode)
    if not article.valid:
        return None, None

    # abort early if year is undesired
    if config.pubmed_year is not None:
        if article.year not in config.pubmed_year:
            return None, None
    if article.title is None:
        print("title is None "+str(article.pmid))
        print(str(article))
    if article.abstract is None:
        print("abstract is None "+str(article.pmid))
        print(str(article))

    data = article.title + " " + article.abstract
    if len(data) < config.pubmed_length:
        return None, None

    result = dict(title=article.title, data=data)
    result["aux_pos"] = "; ".join(article.keywords)
    result["aux_neg"] = ""
    metadata = dict(journal=article.journal, year=article.year)
    result["metadata"] = metadata

    if config.pubmed_pattern is not None:
        if not config.pubmed_pattern.search(str(result)):
            return None, None

    return article.pmid, result


def build_pubmed_items(config, xmlnode, used_ids=set()):
    """Transfer data from pubmed baseline xmls into a crossmap dict

    :param config: dictionary with settings
    :param xmlnode: XML node, expected liked <PubmedArticle>
    :param used_ids: optional set, tracks used ids and skips items already used
    :return: dict with one entry per article
    """

    result = dict()
    for entry in xmlnode.getchildren():
        for metadata in entry.getchildren():
            if metadata.tag != "MedlineCitation":
                continue
            id, article = build_pubmed_one(config, metadata)
            if id is None or id in used_ids:
                continue
            used_ids.add(id)
            result["PMID:" + str(id)] = article

    return result


def build_config(config):
    """prepare raw settings into sets and integers"""

    if config.pubmed_year is not None:
        config.pubmed_year = set(parse_indexes(config.pubmed_year))
    if config.pubmed_pattern is not None:
        config.pubmed_pattern = re.compile(config.pubmed_pattern, re.IGNORECASE)
    config.pubmed_length = int(config.pubmed_length)

    return config


def build_pubmed_dataset(config):
    """create a new dataset file by scanning pubmed baseline files"""

    config = build_config(config)
    baseline_dir = ensure_dir(join(config.outdir, "baseline"))
    baseline_files = listdir(baseline_dir)
    baseline_files.sort(reverse=True)

    out_file = join(config.outdir, config.name+".yaml.gz")
    used_ids = set()
    with gzip.open(out_file, "wt") as out:
        for f in baseline_files:
            if not f.endswith(".xml.gz"):
                continue
            logging.info("Processing: " + f)
            xml = load_xml(join(baseline_dir, f))
            data = build_pubmed_items(config, xml, used_ids)
            if len(data) == 0:
                continue
            out.write(yaml.dump(data))
