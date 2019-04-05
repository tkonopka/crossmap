"""Interface to using crossmap with ontologies.

@author: Tomasz Konopka
"""

import argparse
import gzip
import logging
import yaml
from os import getcwd
from os.path import join
from .obo.obo import Obo


parser = argparse.ArgumentParser(description="crossprep-obo")
parser.add_argument("action", action="store",
                    help="name of utility",
                    choices=["build"])

# inputs for utility: build
parser.add_argument("--obo", action="store", required=True,
                    help="path to obo file",
                    default=None)
parser.add_argument("--name", action="store", required=True,
                    help="name of output dataset",
                    default="obo")
parser.add_argument("--root", action="store",
                    help="filtering by root node",
                    default=None)

# outputs
parser.add_argument("--outdir", action="store", required=True,
                    help="Output directory",
                    default=getcwd())

# ############################################################################

logging.basicConfig(format='[%(asctime)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    level=logging.INFO)

def name_def(term):
    """get a term name and def"""

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


def build_dataset(obo_file, root_id=None):
    """transfer data from an obo into a dictionary"""

    obo = Obo(obo_file)
    if root_id is None:
        hits = set(obo.ids())
    else:
        hits = obo.descendants(root_id)

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
                          auxiliary=" ".join(auxiliary),
                          metadata=metadata)

    return result


if __name__ == "__main__":
    
    config = parser.parse_args()

    logging.info("Starting "+config.action)
    
    if config.action == "build":
        result = build_dataset(config.obo, config.root)
        out_file = join(config.outdir, config.name+".yaml.gz")
        with gzip.open(out_file, "wt") as out:
            out.write(yaml.dump(result))

    logging.info("Done")
