"""
Build a dataset of crossmap using obo files.
"""

from .obo import Obo


def comment(term):
    """helper to get a string with the comment string for an obo term"""

    if term.data is None or "comment" not in term.data:
        return ""
    return ", ".join(term.data["comment"])


def synonyms(term):
    """helper to extract synonyms"""

    if term.data is None or len(term.synonyms) == 0:
        return ""
    return ", ".join(term.synonyms)


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

        result = term.name
        if term.data is None:
            return result
        if "def" in term.data:
            defstr = "".join(term.data["def"])
            defstr = (defstr.split("["))[0].strip()
            if defstr.startswith('"') and defstr.endswith('"'):
                defstr = defstr[1:-1]
            result += self.sep + defstr
        if extras:
            if self.aux_comments:
                result += self.sep + comment(term)
            if self.aux_synonyms:
                result += self.sep + synonyms(term)
        return result.strip()

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
            data = self.content(term, extras=False)
            data_pos = []
            data_neg = []
            metadata = dict()
            if aux_comments:
                data_pos.append(comment(term))
            if aux_synonyms:
                data_pos.append(synonyms(term))
            if aux_top:
                for ancestor in obo.ancestors(id):
                    if ancestor in self.top:
                        data_pos.append(obo.terms[ancestor].name)
            if aux_ancestors:
                metadata["ancestors"] = []
                for ancestor in obo.ancestors(id):
                    metadata["ancestors"].append(ancestor)
                    data_pos.append(content(obo.terms[ancestor]))
            elif aux_parents:
                metadata["parents"] = []
                for parent in obo.parents(id):
                    metadata["parents"].append(parent)
                    data_pos.append(content(obo.terms[parent]))
            if aux_parents and (term.data is None or "def" not in term.data):
                grandparents = set()
                for parent in obo.parents(id):
                    grandparents.update(obo.parents(parent))
                for grandparent in grandparents:
                    data_pos.append(content(obo.terms[grandparent]))
            if aux_siblings:
                for sibling in obo.siblings(id):
                    data_neg.append(obo.terms[sibling].name)
            if aux_children:
                for child in obo.children(id):
                    data_neg.append(obo.terms[child].name)

            # clean up and create object
            data_pos = [_ for _ in data_pos if _ != ""]
            data_neg = [_ for _ in data_neg if _ != ""]
            result[id] = dict(title=term.name,
                              data=data,
                              aux_pos="; ".join(data_pos),
                              aux_neg="; ".join(data_neg),
                              metadata=metadata)
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
