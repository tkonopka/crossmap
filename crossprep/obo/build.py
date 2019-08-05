"""Build a dataset of crossmap using obo files.
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


def build_obo_dataset(obo_file, root_id=None, aux_pos=True, aux_neg=True):
    """transfer data from an obo into a dictionary"""

    obo = Obo(obo_file)
    if root_id is None:
        hits = set(obo.ids())
    else:
        hits = set(obo.descendants(root_id))
        hits.add(root_id)

    result = dict()
    for id in obo.ids():
        if id not in hits:
            continue
        term = obo.terms[id]
        data = name_def(term)
        data_pos = []
        data_neg = []
        metadata = dict(is_a=[])
        for parent in obo.parents(id):
            metadata["is_a"].append(parent)
            if aux_pos:
                data_pos.append(name_def(obo.terms[parent]))
        if aux_neg:
            # only consider words in siblings that are not in term or parents
            temp_neg = []
            for sib in obo.siblings(id):
                temp_neg.append(obo.terms[sib].name)
            all_pos = set((data+" "+" ".join(data_pos)).split(" "))
            all_pos.update(name_def(term, " ").split(" "))
            all_neg = set((" ".join(temp_neg)).split(" "))
            data_neg = all_neg.difference(all_pos)
        result[id] = dict(data=data,
                          aux_pos="; ".join(data_pos),
                          aux_neg="; ".join(data_neg),
                          metadata=metadata)
    return result
