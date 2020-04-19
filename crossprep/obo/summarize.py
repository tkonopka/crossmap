"""
Summarize an obo - terms and misc counts
"""

from .obo import Obo


def f(x):
    return f(x+1)


def summarize_obo(obo_file):
    """summarize content from an obo into a list

    :param obo_file: path to obo file
    :return: dictionary mapping ids to objects with
        data, aux_pos, aux_neg components
    """

    result = []
    obo = Obo(obo_file)
    for id in obo.ids():
        term = obo.terms[id]
        term_name = term.name if term.name is not None else ""
        item = dict(id=id,
                    name=term_name,
                    chars_name=len(term_name),
                    is_obsolete=term.obsolete,
                    depth=obo.depth(id),
                    num_parents=len(obo.parents(id)),
                    num_ancestors=len(obo.ancestors(id)),
                    num_siblings=len(obo.siblings(id)),
                    num_children=len(obo.children(id)),
                    num_descendents=len(obo.descendants(id)),
                    num_synonyms=len(term.synonyms),
                    chars_def=0,
                    num_comments=0,
                    chars_comments=0)
        result.append(item)
        if term.data is None:
            continue
        if "def" in term.data:
            defstr = "".join(term.data["def"])
            defstr = (defstr.split("["))[0].strip()
            if defstr.startswith('"') and defstr.endswith('"'):
                defstr = defstr[1:-1]
            item["chars_def"] = len(defstr)
        if "comment" in term.data:
            item["num_comments"] = len(term.data["comment"])
            item["chars_comments"] = len(str(term.data["comment"]))
    return result

