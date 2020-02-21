"""
Build a dataset for crossmap from opentargets json-like downloads
"""

import gzip
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


def build_opentargets_dataset(associations_path, out_path=None):
    """create a dict containing gene-disease associations

    :param associations_path: character, path to json-like file
    :return: dictionary
    """

    open_fn = gzip.open
    if not associations_path.endswith(".gz"):
        open_fn = open

    # either create a dict in memory, or write into a stream
    if out_path is None:
        result = dict()
        with open_fn(associations_path, "rt") as f:
            for line in f:
                id, item = build_one_association(loads(line))
                result[id] = item
        return result

    with gzip.open(out_path, "wt") as out:
        with open_fn(associations_path, "rt") as f:
            for line in f:
                id, item = build_one_association(loads(line))
                out.write(dump({id: item}))

    return out_path

