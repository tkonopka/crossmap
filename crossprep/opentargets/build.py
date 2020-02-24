"""
Build a dataset for crossmap from opentargets json-like downloads
"""

import gzip
import sys
from json import loads
from yaml import dump


class OpentargetsRawAssociation:
    """container with parsing capabilities"""

    def __init__(self, data):
        self.disease_id = None
        self.disease = None
        self.gene_id = None
        self.gene_symbol = None
        self.gene_name = None
        self.small_molecule = None
        self.antibody = None
        self.parse(data)

    def parse(self, data):
        """assign values into the object from an opentargets object"""

        # shortcuts to parts of the data
        target = data["target"]
        disease = data["disease"]
        if "tractability" in target:
            for k, v in target["tractability"].items():
                v_top = v["top_category"].replace("__", ", ")
                v_top = v_top.replace("_", " ")
                if v_top == "Unknown":
                    continue
                if k == "smallmolecule":
                    self.small_molecule = v_top
                elif k == "antibody":
                    self.antibody = v_top
        if "gene_info" in target:
            self.gene_symbol = target["gene_info"]["symbol"]
            self.gene_name = target["gene_info"]["name"]
            self.gene_id = target["id"]
        if "efo_info" in disease:
            if "label" in disease["efo_info"]:
                self.disease = disease["efo_info"]["label"]
            self.disease_id = disease["id"]


class OpentargetsAssociationsGroup:
    """container for associations between diseases and genes"""

    def __init__(self, association_type="small molecule"):
        self.disease_ids = []
        self.diseases = []
        self.association_type = association_type
        self.genes = []
        self.gene_ids = []
        self.gene_symbols = []

    def add_gene(self, gene_id, gene_symbol, gene_name):
        self.genes.append(gene_symbol + ", " + gene_name)
        self.gene_ids.append(gene_id)
        self.gene_symbols.append(gene_symbol)

    def add_disease(self, disease_id, disease):
        self.disease_ids.append(disease_id)
        self.diseases.append(disease)

    def crossmap_item(self, association_type="gene"):
        """prepare an id and data item for crossmap"""
        tt = self.association_type
        data = {"tractability": tt}
        if association_type == "gene":
            id = "OT:" + tt.replace(" ", "_") + "-" + self.gene_ids[0]
            gene_symbol = self.genes[0].split(",")[0]
            title = "Diseases linked to " + gene_symbol + ", via " + tt
            data["gene"] = self.genes[0]
            data["disease"] = self.diseases
        else:
            id = "OT:" + tt.replace(" ", "_") + "-" + self.disease_ids[0]
            title = tt + " targets for " + self.diseases[0]
            data["gene"] = self.gene_symbols
            data["disease"] = self.diseases[0]
        metadata = {"id": id,
                    "gene_id": self.gene_ids,
                    "disease_id": self.disease_ids}
        return id, {"title": title, "data": data, "metadata": metadata}

    def __str__(self):
        result = {"disease_ids": self.disease_ids,
                  "diseases": self.diseases,
                  "association_type": self.association_type,
                  "gene_ids": self.gene_ids,
                  "genes": self.genes}
        return str(result)


class OpentargetsDiseaseAssociations(OpentargetsAssociationsGroup):
    """subclass of container that permits only one disease"""

    def add_disease(self, disease_id, disease):
        if len(self.disease_ids) == 0:
            self.disease_ids.append(disease_id)
            self.diseases.append(disease)


class OpentargetsGeneAssociations(OpentargetsAssociationsGroup):
    """subclass of container that permits only one gene"""

    def add_gene(self, gene_id, gene_symbol, gene_name):
        if len(self.gene_ids) == 0:
            self.gene_ids.append(gene_id)
            self.genes.append(gene_symbol + ", " + gene_name)


def build_opentargets_dataset(associations_path, disease_prefix,
                              association_type="gene", out=sys.stdout):
    """create a dict containing gene-disease associations

    :param associations_path: character, path to json-like file
    :param disease_prefix: prefix for disease ids (other associations ignored)
    :param type: string, use "gene" or "disease"
    :param out: output stream
    :return: dictionary
    """

    open_fn = gzip.open
    if not associations_path.endswith(".gz"):
        open_fn = open

    result = dict()
    assoc_class = OpentargetsDiseaseAssociations
    if association_type == "gene":
        assoc_class = OpentargetsGeneAssociations
    with open_fn(associations_path, "rt") as f:
        for line in f:
            item = OpentargetsRawAssociation(loads(line))
            if not item.disease_id.startswith(disease_prefix):
                continue
            assoc_id = item.disease_id
            if association_type == "gene":
                assoc_id = item.gene_id
            sm_id = "OT:small_molecule_" + assoc_id
            ab_id = "OT:antibody_" + assoc_id
            if sm_id not in result:
                result[sm_id] = assoc_class()
            if ab_id not in result:
                result[ab_id] = assoc_class()
            if item.small_molecule is not None:
                result[sm_id].add_gene(item.gene_id, item.gene_symbol,
                                       item.gene_name)
                result[sm_id].add_disease(item.disease_id, item.disease)
            if item.antibody is not None:
                result[ab_id].add_gene(item.gene_id, item.gene_symbol,
                                       item.gene_name)
                result[ab_id].add_disease(item.disease_id, item.disease)
    for _, v in result.items():
        if len(v.gene_ids) == 0:
            continue
        item_id, item = v.crossmap_item(association_type)
        out.write(dump({item_id: item}))

