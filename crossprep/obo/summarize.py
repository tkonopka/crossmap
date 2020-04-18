"""
Summarize an obo - terms and misc counts
"""

import sys
from yaml import dump
from .obo import Obo


def summarize_obo(obo_file):
    """summarize content from an obo into a list

    :param obo_file: path to obo file
    :param root_id: character, id of root node. This can be used to
        build a dataset for an ontology branch
    :return: dictionary mapping ids to objects with
        data, aux_pos, aux_neg components
    """

    result = []
    obo = Obo(obo_file)
    for id in obo.ids():
        term = obo.terms[id]
        item = dict(id=id, name=term.name)
        result.append(item)
        item["is_obsolete"] = term.obsolete
        item["num_parents"] = len(obo.parents(id))
        item["num_siblings"] = len(obo.siblings(id))
        item["num_children"] = len(obo.children(id))
        item["num_synonyms"] = len(term.synonyms)
        # keys that are filled from the term.data
        item["chars_def"] = 0
        item["num_comments"] = 0
        item["chars_comments"] = 0
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

