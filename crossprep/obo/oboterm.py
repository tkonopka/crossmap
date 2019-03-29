""" Class holding a single term defined in an obo file.

This container/parser only supports a few of the data types in an obo term. 

(This file is copied from another project: Phenoscoring)

@author: Tomasz Konopka
"""


## ##################################################################
# Container for an ontology term
# To use this, create an object, then add data to it. 


class MinimalOboTerm():
    """A container holding just minimal information on an ontology term"""

    def __init__(self):
        """create a small set of empty fields"""
        self.id = None
        self.obsolete = False
        self.relations = []

    def valid(self):
        """Use this to query if the object is well formed."""

        return self.id is not None

    def parse(self, datastr):
        """parse one line of data from a string

        Arguments:
            datastr   character string, single line from an obo file
            minimal   boolean, if True, parsing will skip some steps
        """

        if datastr == "":
            return
        tokens = datastr.split(": ", 1)

        # handle core items
        if tokens[0] == "id":
            self.id = tokens[1]
            return
        if tokens[0] == "is_obsolete":
            if tokens[1] == "true":
                self.obsolete = True
            else:
                raise Exception("Unknown value for field is_obsolete")
            return
        if tokens[0] == "is_a":
            self.add_relation(tokens[1], "is_a")
            return

    def add_relation(self, parent, relation):
        """Add a relation to the term."""

        parent = parent.split(" ", 1)[0]
        self.relations.append((relation, parent))

    def __str__(self):
        """a quick summary of this term."""
        obs = str(self.obsolete)
        return "OboTerm: "+ self.id+", obsolete: "+obs


class OboTerm(MinimalOboTerm):
    """A container for a generic obo term, with more stored fields"""
    
    def __init__(self):
        """Initiate an object with empty fields."""

        super(OboTerm, self).__init__()
        self.name = None
        self.synonyms = set()
        self.data = None

    def valid(self):
        """Use this to query if the object is well formed."""        

        # currently this only test for an existing id.
        # Perhaps this could be expanded to check for name and relationships
        if self.id is None:
            return False
        return True

    def parse(self, datastr):
        """parse one line of data from a string

        Arguments:
            datastr   character string, single line from an obo file
            minimal   boolean, if True, parsing will skip some steps
        """
                
        if datastr == "":
            return
        tokens = datastr.split(": ", 1)

        # handle some cases by previous code
        if tokens[0] in ("id", "is_a", "is_obsolete"):
            super(OboTerm, self).parse(datastr)
            return
        if tokens[0] == "name":
            self.name = tokens[1]
            return
        if tokens[0] == "synonym":
            self.add_synonym(tokens[1])
            return
        if self.data is None:
            self.data = dict()
        if tokens[0] not in self.data:
            self.data[tokens[0]] = set()
        self.data[tokens[0]].add(tokens[1])

    def add_synonym(self, synonym):
        """Add a definition of a synonym to this object."""
        
        if self.name is None:
            raise Exception("Error parsing synonym; term name is not set")
        
        # Extract value between quotes
        secondq = synonym.find('"', 2)
        if secondq > 0:
            synonym = synonym[1:secondq]
        if synonym == self.name:
            return
        self.synonyms.add(synonym)

    def __str__(self):
        """a quick summary of this term."""
        obs = str(self.obsolete)
        return "OboTerm: "+ self.id+", "+self.name + ", obsolete: "+obs
