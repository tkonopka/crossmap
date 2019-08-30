"""
Build a dataset for crossmap from orphanet xmls
"""

import xml.etree.ElementTree as XML


class OrphanetDisorderGenes:
    """Container for disease gene associations"""

    def __init__(self, node):
        """create a new container, parse data from an xml node"""

        self.id = 0
        self.name = ""
        self.genes = []
        self.hgnc = []
        self.ensembl = []

        for child in node:
            if child.tag == "OrphaNumber":
                self.id = child.text
            elif child.tag == "Name":
                self.name = child.text
            elif child.tag == "DisorderGeneAssociationList":
                self._parse_association_list(child)

    def _parse_association_list(self, node):
        for child in node:
            if child.tag != "DisorderGeneAssociation":
                continue
            self._parse_association(child)

    def _parse_association(self, node):
        for child in node:
            if child.tag != "Gene":
                continue
            self._parse_gene(child)

    def _parse_gene(self, node):
        result = ["", ""]
        for child in node:
            if child.tag == "Name":
                result[1] = child.text
            elif child.tag == "Symbol":
                result[0] = child.text
            elif child.tag == "ExternalReferenceList":
                self._parse_external_reflist(child)
        self.genes.append(result)

    def _parse_external_reflist(self, node):
        for child in node:
            if child.tag != "ExternalReference":
                continue
            source = ""
            number = ""
            for subchild in child:
                if subchild.tag == "Source":
                    source = subchild.text
                elif subchild.tag == "Reference":
                    number = subchild.text
            if source == "HGNC":
                self.hgnc.append("HGNC:" + str(number))
            if source == "Ensembl":
                self.ensembl.append(str(number))

    def __str__(self):
        return str(self.id)+"; "+str(self.genes)


class OrphanetDisorderPhenotypes:
    """Container for disease phenotypes."""

    def __init__(self, node):
        """Create a new disease container, parse data from an xml node."""

        self.id = 0
        self.name = ""
        self.phenotypes = []

        for child in node:
            if child.tag == "OrphaNumber":
                self.id = child.text
            elif child.tag == "Name":
                self.name = child.text
            elif child.tag == "HPODisorderAssociationList":
                self._parse_association_list(child)

    def _parse_association_list(self, node):
        """parse a node with an association list"""

        result = []
        for child in node:
            if child.tag != "HPODisorderAssociation":
                continue
            result.append(self._parse_association(child))

    def _parse_association(self, node):
        """parse a node with association"""

        result = ["", ""]
        for child in node:
            if child.tag != "HPO":
                continue
            for subchild in child:
                if subchild.tag == "HPOId":
                    result[0] = subchild.text
                elif subchild.tag == "HPOTerm":
                    result[1] = subchild.text
        self.phenotypes.append(result)

    def __str__(self):
        return str(self.id)+"; "+str(self.name)+"; "+str(self.phenotypes)


def combine_phenotypes_genes(phen_data, gene_data):
    """Transfer data for objects into a crossmap format

    :param phen_data: dict mapping ids to OrphanetDisorderPhenotypes
    :param gene_data: dict mapping ids to OrphanetDisorderGenes
    :return: dict with a crossmap dataset
    """

    # create blank entries for all disorders
    result = dict()
    all_ids = list(phen_data.keys())
    all_ids.extend(gene_data.keys())
    for id in all_ids:
        result["ORPHA:"+str(id)] = dict(title="", data="",
                                        aux_pos=[], metadata=dict())

    # transfer information about phenotypes and genes
    for disorder in phen_data.values():
        terms = [_[1] for _ in disorder.phenotypes]
        ids = [_[0] for _ in disorder.phenotypes]
        data = result["ORPHA:" + str(disorder.id)]
        data["title"] = data["data"] = disorder.name
        data["aux_pos"].extend(terms)
        data["metadata"]["phenotype_ids"] = ids
    for disorder in gene_data.values():
        genes = [_[0] + " - " + _[1] for _ in disorder.genes]
        data = result["ORPHA:" + str(disorder.id)]
        if data["data"] == "":
            data["title"] = data["data"] = disorder.name
        data["aux_pos"].extend(genes)
        data["metadata"]["hgnc"] = disorder.hgnc
        data["metadata"]["ensembl"] = disorder.ensembl
    return result


def build_orphanet_dataset(phenotypes_path, genes_path):
    """create a dict containing data individual orphanet discorder

    :param phenotypes_path: character, path to xml with disorder-phenotypes
    :param genes_path: character, path to xml with disorder gene associations
    :return: dictionary
    """

    phen_data, gene_data = dict(), dict()
    # parse the phenotype data, then gene data
    phenotypes_root = XML.parse(phenotypes_path).getroot()
    for n1 in phenotypes_root:
        if n1.tag != "DisorderList":
            continue
        for disorder in n1:
            data = OrphanetDisorderPhenotypes(disorder)
            phen_data[data.id] = data
    genes_root = XML.parse(genes_path).getroot()
    for n1 in genes_root:
        if n1.tag != "DisorderList":
            continue
        for disorder in n1:
            data = OrphanetDisorderGenes(disorder)
            gene_data[data.id] = data
    # create dataset
    return combine_phenotypes_genes(phen_data, gene_data)

