"""tools associated with crossprep
"""

import gzip
import yaml
from os.path import join


def save_dataset(data, dir, name):
    """write a dictionary with data to a crossmap file"""

    out_file = join(dir, name+".yaml.gz")
    with gzip.open(out_file, "wt") as out:
        out.write(yaml.dump(data))

