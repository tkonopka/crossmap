"""Parsing ontologies from obo files on disk.

(This file is copied from another project: phenoscoring)
"""

from .oboterm import OboTerm, MinimalOboTerm


# ############################################################################
# Container for an ontology, constructed from an obo definition file

class MinimalObo:
    """Representation of an obo ontology with minimal parsing and checking"""

    def __init__(self, filepath, infer_children=True):
        """Initiate by parsing an obo file

         Arguments:
             filepath        path to obo file on disk
             infer_children  logical, precompute parent/child relations
        """

        self.terms = parse_obo(filepath, MinimalOboTerm)
        self.parents_cache = dict()
        self.ancestors_cache = dict()
        self.descendants_cache = dict()
        self.clear_cache()
        if infer_children:
            add_parent_of(self)

    def clear_cache(self):
        self.parents_cache = dict()
        self.ancestors_cache = dict()
        self.descendants_cache = dict()

    def ids(self, including_obsolete=False):
        """Fetch a set of terms defined in the ontology."""

        allterms = list(self.terms.keys())
        if including_obsolete:
            return allterms

        return [_ for _ in allterms if not self.terms[_].obsolete]

    def has(self, key):
        """determine if obo object contains a term with given key."""

        return key in self.terms

    def valid(self, key):
        """determine if key is in the ontology and is not obsolete."""

        if not self.has(key):
            return False
        return not self.terms[key].obsolete

    def parents(self, key):
        """Retrieve all parents of a term, as a tuple (uses cache)."""

        if key in self.parents_cache:
            return self.parents_cache[key]
        result = get_by_relation(self, key, "is_a")
        self.parents_cache[key] = result
        return result

    def ancestors(self, key):
        """retrieve ancestors (parents, parents thereof, etc) (uses cache)

        Returns:
            set with ancestors
        """

        if key in self.ancestors_cache:
            return self.ancestors_cache[key]
        result = get_by_relation_recursive(self, key, "is_a")
        self.ancestors_cache[key] = result
        return self.ancestors(key)

    def children(self, key):
        """Retrieve all the children of a term."""

        return get_by_relation(self, key, "parent_of")

    def descendants(self, key):
        """Retrieve all children down to leaves (uses cache)"""

        if key in self.descendants_cache:
            return self.descendants_cache[key]
        result = get_by_relation_recursive(self, key, "parent_of")
        self.descendants_cache[key] = result
        return result

    def siblings(self, key):
        """Retrieve siblings of a given term."""

        # look for siblings by going up one, down one in tree
        parents = self.parents(key)
        result = set()
        for p in parents:
            for sibling in self.children(p):
                result.add(sibling)
        # remove itself (the if condition should always be positive)
        if key in result:
            result.remove(key)
        return tuple(result)

    def sim_jaccard(self, key1, key2):
        """Compute similarity of two terms using ancestors. """

        a1 = set(self.ancestors(key1))
        a2 = set(self.ancestors(key2))
        a1.add(key1)
        a2.add(key2)
        return len(a1.intersection(a2)) / len(a1.union(a2))


class Obo(MinimalObo):
    """Representation of an obo ontology.

    Compared to MinimalObo, this attempts to hold all data from an obo file.
    """

    def __init__(self, filepath, infer_children=True):
        """Initiate by parsing an obo file

         Arguments:
             filepath        path to obo file on disk
             infer_children  logical, precompute parent/child relations
             minimal         logical, to parse all obo fields (False),
                or skip non-essentials like synonyms, defs, others (False)
        """

        self.terms = parse_obo(filepath, OboTerm)
        self.clear_cache()
        if infer_children:
            add_parent_of(self)

    def name(self, key):
        """Retrieve the name associated with an id/key."""

        if key not in self.terms:
            return None
        else:
            return self.terms[key].name


# ############################################################################
# Helper functions for this module


def get_by_relation(obo, key, relation):
    """Identify all hits for a relation type."""
            
    if key not in obo.terms:
        raise Exception("key "+str(key)+" not present in ontology")
    
    term = obo.terms[key]
    result = set()
    for type, target in term.relations:
        if type == relation and obo.valid(target):                
            result.add(target)        
    return tuple(result)            


def get_by_relation_recursive(obo, key, relation):
    """Identify all hits for a relation type, recursively
    
    Return:
        set of identifiers that are related to the key
    """
                
    def get_recursive(x):               
        if x in result or x in visited:
            return
        result.add(x)
        visited.add(x)                        
        for hit in get_by_relation(obo, x, relation):
            get_recursive(hit)
        
    result, visited = set(), set()    
    get_recursive(key)
    result.remove(key)    
    return tuple(result)      


def add_parent_of(obo):
    """Augment the relations in an Obo to include 'parent_of'."""
    
    for child in obo.ids(True):            
        for parent in obo.parents(child):
            obo.terms[parent].add_relation(child, "parent_of")


def parse_obo(filename, OboTermClass=OboTerm):
    """Helper to parse an obo file and transfer data into dicts"""

    result = dict()

    state = None
    newterm = None              
    with open(filename, "r") as f:
        for line in f:            
            line = line[:-1]
                        
            # set the state of the parser
            if line == "[Term]" or line == "[Typedef]":
                state = line

            # early stopping conditions and transitions between terms
            if state != "[Term]":
                continue
            if line == "" and newterm is not None:
                if newterm.valid():                           
                    result[newterm.id] = newterm
                    newterm = None
                    continue
                else:
                    raise Exception("Incomplete [Term]")
            if line == "[Term]":                
                newterm = OboTermClass()
                continue
             
            # add information into the term
            newterm.parse(line)
                                                       
    return result

