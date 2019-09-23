"""
Build a dataset of crossmap using obo files.
"""

from .obo import Obo


def name_def(term, sep="; "):
    """helper to get a string with term name and def"""

    result = term.name
    if term.data is None:
        return result
    if "def" in term.data:
        defstr = "".join(term.data["def"])
        defstr = (defstr.split("["))[0].strip()
        if defstr.startswith('"') and defstr.endswith('"'):
            defstr = defstr[1:-1]
        if not defstr.endswith("."):
            defstr += "."
        result += sep + defstr
    return result


def build_obo_dataset(obo_file, root_id=None, aux="none"):
    """transfer data from an obo into a dictionary

    :param obo_file: path to obo file
    :param root_id: character, id of root node. This can be used to
        build a dataset for an ontology branch
    :param aux: character, the type of data to include in
        aux_pos and aux_neg fields
    :return:
    """

    obo = Obo(obo_file)
    if root_id is None:
        hits = set(obo.ids())
    else:
        hits = set(obo.descendants(root_id))
        hits.add(root_id)

    aux_parents = ("parents" in aux)
    aux_ancestors = ("ancestors" in aux)
    aux_siblings = ("siblings" in aux)
    aux_children = ("children" in aux)

    result = dict()
    for id in obo.ids():
        if id not in hits:
            continue
        term = obo.terms[id]
        data = name_def(term)
        data_pos = []
        data_neg = []
        metadata = dict()
        if aux_parents:
            metadata["parents"] = []
            for parent in obo.parents(id):
                metadata["parents"].append(parent)
                data_pos.append(name_def(obo.terms[parent]))
        if aux_ancestors:
            metadata["ancestors"] = []
            for ancestor in obo.ancestors(id):
                metadata["ancestors"].append(ancestor)
                data_pos.append(name_def(obo.terms[ancestor]))
        if aux_siblings:
            for sibling in obo.siblings(id):
                data_neg.append(obo.terms[sibling].name)
        if aux_children:
            for child in obo.children(id):
                data_neg.append(obo.terms[child].name)
        result[id] = dict(title=term.name,
                          data=data,
                          aux_pos="; ".join(data_pos),
                          aux_neg="; ".join(data_neg),
                          metadata=metadata)
    return result
