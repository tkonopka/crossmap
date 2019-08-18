"""Build a dataset for crossmap from orphanet xmls
"""

import gzip
import yaml
from os.path import join
import xml.etree.ElementTree as XML


class OrphanetDisorder:
    """Container for disease data."""

    def __init__(self, node):
        """Create a new disease container, parse data from an xml node."""

        self.id = 0
        self.name = ""
        self.phenotypes = []

        for c in node.getchildren():
            if c.tag == "OrphaNumber":
                self.id = c.text
            elif c.tag == "Name":
                self.name = c.text
            elif c.tag == "HPODisorderAssociationList":
                self._parse_association_list(c)

    def _parse_association_list(self, node):
        """parse a node with an association list"""

        result = []
        for c in node:
            if c.tag != "HPODisorderAssociation":
                continue
            result.append(self._parse_association(c))

    def _parse_association(self, node):
        """parse a node with association"""

        result = ["", ""]
        for c in node:
            if c.tag != "HPO":
                continue
            for subc in c:
                if subc.tag == "HPOId":
                    result[0] = subc.text
                elif subc.tag == "HPOTerm":
                    result[1] = subc.text
        self.phenotypes.append(result)

    def __str__(self):
        return str(self.id)+"; "+str(self.name)+"; "+str(self.phenotypes)


def build_disorder(xmlnode):
    """Transfer data for one disease into a dict

    Arguments:
        xmlnode   XML node, expected like <Disorder>

    Returns:
        a string id and a dict with data
    """

    disorder = OrphanetDisorder(xmlnode)
    terms = [_[1] for _ in disorder.phenotypes]
    ids = [_[0] for _ in disorder.phenotypes]
    metadata = dict(num_phenotypes=len(ids),
                    phenotype_ids=ids)
    result = dict(data="ORPHA:"+disorder.id + " " + disorder.name,
                  aux_pos=terms,
                  metadata=metadata)
    return "ORPHA:" + str(disorder.id), result


def build_orphanet(filepath):
    """create a dict containing the content of an orphanet dataset"""

    result = dict()
    fileroot = XML.parse(filepath).getroot()
    for n1 in fileroot:
        if n1.tag != "DisorderList":
            continue
        for disorder in n1:
            id, data = build_disorder(disorder)
            result[id] = data
    return result


def build_orphanet_dataset(config):
    """write a new dataset file by parsing from an orphanet xml"""

    result = build_orphanet(config.input)
    out_file = join(config.outdir, config.name+".yaml.gz")
    with gzip.open(out_file, "wt") as out:
        out.write(yaml.dump(result))

