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
            if child.tag in ("OrphaNumber", "OrphaCode"):
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
            if child.tag in ("OrphaNumber", "OrphaCode"):
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

        result = ["", "", ""]
        for child in node:
            if child.tag == "HPO":
                for subchild in child:
                    if subchild.tag == "HPOId":
                        result[0] = subchild.text
                    elif subchild.tag == "HPOTerm":
                        result[1] = subchild.text
            if child.tag == "HPOFrequency":
                for subchild in child:
                    if subchild.tag == "Name":
                        result[2] = subchild.text
        self.phenotypes.append(result)

    def __str__(self):
        return str(self.id)+"; "+str(self.name)+"; "+str(self.phenotypes)


class OrphanetDisorder:
    """Container for disease description"""

    def __init__(self, node):
        """create a new container, parse data from an xml node"""

        self.id = 0
        self.name = ""
        self.description = []
        self.status = None

        info_lists = ("TextualInformationList", "SummaryInformationList")
        for child in node:
            if child.tag in ("OrphaNumber", "OrphaCode"):
                self.id = child.text
            if child.tag == "Name":
                self.name = child.text
            if child.tag == "Totalstatus":
                self.status = child.text
            elif child.tag in info_lists:
                self._parse_textinfo_list(child)

    def _parse_textinfo_list(self, node):
        info_fields = ("TextualInformation", "SummaryInformation")
        for child in node:
            if child.tag in info_fields:
                self._parse_textinfo(child)

    def _parse_textinfo(self, node):
        for child in node:
            if child.tag == "TextSectionList":
                self._parse_textsection_list(child)

    def _parse_textsection_list(self, node):
        for child in node:
            if child.tag == "TextSection":
                self._parse_textsection(child)

    def _parse_textsection(self, node):
        for child in node:
            if child.tag == "Contents":
                self.description.append(child.text)

    def __str__(self):
        return str(self.id)+"; "+str(self.description)


def orpha_id(id):
    return "ORPHA:" + str(id)


def disorder_phenotypes(disorder, excluded=False):
    """prepare lists of phenotype ids and names

    :param disorder: OrphanetDisorderPhenotypes object
    :param excluded: logical, set True to get results for excluded phenotypes
    :return: two arrays with phenotype ids and names
    """
    ids, terms = [], []
    for phenotype in disorder.phenotypes:
        phen_id, term, freq = phenotype[0], phenotype[1], phenotype[2]
        if excluded and "Excluded" not in freq:
            continue
        if not excluded and "Excluded" in freq:
            continue
        ids.append((phen_id+" "+freq).strip())
        terms.append(term)
    return ids, terms


def combine_phenotypes_genes(phen_data, gene_data, disorder_data):
    """Transfer data for objects into a crossmap format

    :param phen_data: dict mapping ids to OrphanetDisorderPhenotypes
    :param gene_data: dict mapping ids to OrphanetDisorderGenes
    :param disorder_data: dict mapping ids to OrphanetDisorder
    :return: dict with a crossmap dataset
    """

    # create blank entries for all disorders
    all_ids = list(disorder_data.keys())
    result = dict()
    for id in all_ids:
        result[orpha_id(id)] = dict(title="",
                                    data=dict(title="",
                                              description="",
                                              genes=[], phenotypes=[]),
                                    data_neg=dict(phenotypes=[]),
                                    metadata=dict(id=orpha_id(id)))
    all_ids = set(all_ids)

    # transfer information about phenotypes and genes
    for disorder in phen_data.values():
        if disorder.id not in all_ids:
            continue
        ids, terms = disorder_phenotypes(disorder, excluded=False)
        ids_neg, terms_neg = disorder_phenotypes(disorder, excluded=True)
        data = result["ORPHA:" + str(disorder.id)]
        data["title"] = data["data"]["title"] = disorder.name
        data["data"]["phenotypes"].extend(terms)
        data["data_neg"]["phenotypes"].extend(terms_neg)
        data["metadata"]["phenotype_ids"] = ids
        data["metadata"]["neg_phenotype_ids"] = ids_neg
    for disorder in gene_data.values():
        if disorder.id not in all_ids:
            continue
        genes = [_[0] + " - " + _[1] for _ in disorder.genes]
        data = result["ORPHA:" + str(disorder.id)]
        if data["title"] == "":
            data["title"] = data["data"]["title"] = disorder.name
        data["data"]["genes"].extend(genes)
        data["metadata"]["hgnc_ids"] = disorder.hgnc
        data["metadata"]["ensembl_ids"] = disorder.ensembl
    for disorder in disorder_data.values():
        data = result[orpha_id(disorder.id)]
        disorder_desc = ""
        if len(disorder.description) == 1:
            disorder_desc = disorder.description[0]
        elif len(disorder.description) > 1:
            disorder_desc = disorder.description
        data["data"]["description"] = disorder_desc
        data["title"] = data["data"]["title"] = disorder.name
    return result


def build_orphanet_dataset(phenotypes_path, genes_path, nomenclature_path):
    """create a dict containing orphanet discorders

    :param phenotypes_path: character, path to xml with disorder-phenotypes
    :param genes_path: character, path to xml with disorder gene associations
    :param nomenclature_path: character, path to xml with disorder
        descriptions
    :return: dictionary
    """

    phen_data, gene_data, nomenclature_data = dict(), dict(), dict()
    # parse the phenotype data, then gene data
    phenotypes_root = XML.parse(phenotypes_path).getroot()
    for n1 in phenotypes_root:
        # this ugly structure is a patch to handle two file formats (old & new)
        if n1.tag == "HPODisorderSetStatusList":
            for n2 in n1:
                for disorder in n2:
                    if disorder.tag != "Disorder":
                        continue
                    data = OrphanetDisorderPhenotypes(disorder)
                    phen_data[data.id] = data
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
    nomenclature_root = XML.parse(nomenclature_path).getroot()
    for n1 in nomenclature_root:
        if n1.tag != "DisorderList":
            continue
        for disorder in n1:
            data = OrphanetDisorder(disorder)
            if data.status == "Active" and len(data.description) > 0:
                nomenclature_data[data.id] = data
    result = combine_phenotypes_genes(phen_data, gene_data, nomenclature_data)
    return result

