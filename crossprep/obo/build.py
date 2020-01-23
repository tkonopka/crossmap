"""
Build a dataset of crossmap using obo files.
"""

from .obo import Obo


def comments(term):
    """helper to get a string with the comment string for an obo term"""
    if term.data is None or "comment" not in term.data:
        return []
    return term.data["comment"]


def synonyms(term):
    """helper to extract synonyms"""
    if term.data is None or len(term.synonyms) == 0:
        return []
    return list(term.synonyms)


def tops(id, obo, root_ids):
    """helper to extract top term names"""
    result = []
    for ancestor in obo.ancestors(id):
        if ancestor in root_ids:
            result.append(obo.terms[ancestor].name)
    return result


def siblings(id, obo):
    """helper to extract an array of sibling names"""
    result = []
    for sibling in obo.siblings(id):
        result.append(obo.terms[sibling].name)
    return result


def children(id, obo):
    """helper to extract an array of children names"""
    result = []
    for child in obo.children(id):
        result.append(obo.terms[child].name)
    return result


class OboBuilder:
    """Builder of a crossmap dataset from obo"""

    # characters to separate entries, synonyms, etc.
    sep = "; "

    def __init__(self, obo_file, root_id=None, aux="none"):
        """set up an obo object and understand building settings"""

        self.obo = Obo(obo_file)
        self.top = set()
        if root_id is None:
            self.hits = set(self.obo.ids())
        else:
            self.hits = set(self.obo.descendants(root_id))
            self.hits.add(root_id)
            self.top = set(self.obo.children(root_id))

        self.aux_comments = ("comments" in aux)
        self.aux_synonyms = ("synonyms" in aux)
        self.aux_parents = ("parents" in aux)
        self.aux_ancestors = ("ancestors" in aux)
        self.aux_siblings = ("siblings" in aux)
        self.aux_children = ("children" in aux)
        self.aux_top = ("top" in aux)

    def content(self, term, extras=True):
        """helper to get a single string to describe a term"""

        result = dict(name=term.name)
        if term.data is None:
            return result
        if "def" in term.data:
            defstr = "".join(term.data["def"])
            defstr = (defstr.split("["))[0].strip()
            if defstr.startswith('"') and defstr.endswith('"'):
                defstr = defstr[1:-1]
            result["def"] = defstr
        if extras:
            if self.aux_comments:
                result["comments"] = comments(term)
            if self.aux_synonyms:
                result["synonyms"] = synonyms(term)
        return result

    def build(self):
        """transfer data from obo into a dictionary"""

        result = dict()

        # shortcuts
        obo, hits = self.obo, self.hits
        content = self.content
        aux_parents, aux_ancestors = self.aux_parents, self.aux_ancestors
        aux_synonyms, aux_children = self.aux_synonyms, self.aux_children
        aux_siblings = self.aux_siblings
        aux_top, aux_comments = self.aux_top, self.aux_comments

        for id in obo.ids():
            if id not in hits:
                continue
            term = obo.terms[id]
            data_pos = self.content(term, extras=False)
            data_neg = dict()
            metadata = dict()
            if aux_comments:
                data_pos["comments"] = comments(term)
            if aux_synonyms:
                data_pos["synonyms"] = synonyms(term)
            if aux_top:
                data_pos["top"] = tops(id, obo, self.top)
            if aux_ancestors:
                metadata["ancestors"] = []
                data_pos["ancestors"] = []
                for ancestor in obo.ancestors(id):
                    metadata["ancestors"].append(ancestor)
                    data_pos["ancestors"].append(content(obo.terms[ancestor]))
            elif aux_parents:
                metadata["parents"] = []
                data_pos["parents"] = []
                for parent in obo.parents(id):
                    metadata["parents"].append(parent)
                    parent_content = content(obo.terms[parent])
                    for v in parent_content.values():
                        v_str = str(v)
                        if v_str == '' or v_str == '[]':
                            continue
                        data_pos["parents"].append(v_str)
            if aux_parents and (term.data is None or "def" not in term.data):
                grandparents = set()
                data_pos["grandparents"] = []
                for parent in obo.parents(id):
                    grandparents.update(obo.parents(parent))
                for grandpar in grandparents:
                    grandpar_content = content(obo.terms[grandpar])
                    for v in grandpar_content.values():
                        v_str = str(v)
                        if v_str == '' or v_str == '[]':
                            continue
                        data_pos["grandparents"].append(v_str)
            if aux_siblings:
                data_neg["siblings"] = siblings(id, obo)
            if aux_children:
                data_neg["children"] = children(id, obo)

            # clean up and create object
            obj = dict(title=term.name, data_pos=data_pos)
            if len(data_neg):
                obj["data_neg"] = data_neg
            obj["metadata"] = metadata
            result[id] =obj
        return result


def build_obo_dataset(obo_file, root_id=None, aux="none"):
    """transfer data from an obo into a dictionary

    :param obo_file: path to obo file
    :param root_id: character, id of root node. This can be used to
        build a dataset for an ontology branch
    :param aux: character, the type of data to include in
        aux_pos and aux_neg fields
    :return: dictionary mapping ids to objects with
        data, aux_pos, aux_neg components
    """

    builder = OboBuilder(obo_file, root_id, aux)
    return builder.build()
