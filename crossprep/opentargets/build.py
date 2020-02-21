"""
Build a dataset for crossmap from opentargets json-like downloads
"""

import gzip
import sys
from json import loads
from yaml import dump


def build_one_association(data):
    """create an id and object for crossmap from raw opentargets data"""

    # shortcuts to parts of the data
    target = data["target"]
    disease = data["disease"]
    # start constructing parts of the output
    id = "OT:" + data["id"]
    metadata = {"id": id}
    tractability = []
    gene_info, disease_info = "", ""
    if "tractability" in target:
        for k, v in target["tractability"].items():
            v_top = v["top_category"]
            if k == "smallmolecule":
                k = "small molecule"
            if v_top != "Unknown":
                tractability.append(k + " - "+v_top)
    if "gene_info" in target:
        gene_info = target["gene_info"]["symbol"]+" - "+target["gene_info"]["name"]
        metadata["gene_id"] = target["id"]
    if "efo_info" in disease:
        if "label" in disease["efo_info"]:
            disease_info = disease["efo_info"]["label"]
        metadata["disease_id"] = disease["id"]
    data = {"gene": gene_info,
            "disease": disease_info,
            "tractability": tractability}
    return id, {"data": data, "metadata": metadata}


def build_opentargets_dataset(associations_path, disease_prefix, out=sys.stdout):
    """create a dict containing gene-disease associations

    :param associations_path: character, path to json-like file
    :param disease_prefix: prefix for disease ids (other associations ignored)
    :param out: output stream
    :return: dictionary
    """

    open_fn = gzip.open
    if not associations_path.endswith(".gz"):
        open_fn = open

    # either create a dict in memory, or write into a stream
    with open_fn(associations_path, "rt") as f:
        for line in f:
            id, item = build_one_association(loads(line))
            disease_id = item["metadata"]["disease_id"]
            if disease_id.startswith(disease_prefix):
                out.write(dump({id: item}))


