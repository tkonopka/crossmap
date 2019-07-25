"""Build a dataset of crossmap using obo files.
"""

from .obo import Obo


def name_def(term):
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
        result += "; "+defstr
    return result


def build_obo_dataset(obo_file, root_id=None):
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
        auxiliary = []
        metadata = dict(is_a=[])
        for parent in obo.parents(id):
            metadata["is_a"].append(parent)
            auxiliary.append(name_def(obo.terms[parent]))
        result[id] = dict(data=data,
                          aux_pos=" ".join(auxiliary),
                          aux_neg="",
                          metadata=metadata)
    return result
