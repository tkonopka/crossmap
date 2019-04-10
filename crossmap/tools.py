"""Multi-purpose tools

@author: Tomasz Konopka
"""


import yaml
import csv
import pickle


def read_csv_set(filepaths, column, delimiter="\t", quotechar="'"):
    """scan csv files, transfer values from a column into a list"""

    result = set()
    if filepaths is None:
        return result
    if type(filepaths) is str:
        filepaths = [filepaths]

    for filepath in filepaths:
        with open(filepath, "r") as f:
            r = csv.DictReader(f, delimiter=delimiter, quotechar=quotechar)
            for row in r:
                result.add(row[column])

    return result


def write_csv(obj, filepath, delimiter="\t", id_column="id", value_column="count"):
    """write a counter/dict object into a csv file"""

    if type(obj) is set:
        with open(filepath, "wt") as f:
            f.write(id_column + "\n")
            for k in obj:
                f.write(k + "\n")
    else:
        with open(filepath, "wt") as f:
            f.write(id_column + delimiter + value_column + "\n")
            for k, v in obj.items():
                f.write(k + "\t" + str(v) + "\n")


def read_set(filepaths):
    """read lines from a plain text file or files.

    Arguments:
        filepath   string with file path, or iterable with many file paths

    Returns:
        set with file contents
    """

    if filepaths is None:
        return set()
    if type(filepaths) is str:
        filepaths = [filepaths]

    result = set()
    for filepath in filepaths:
        with open(filepath, "r") as f:
            for line in f:
                result.add(line.strip())
    return result


def read_dict(filepath, id_col="id", value_col="index", value_fun=None):
    """read an id-index map from file."""

    result = dict()
    with open(filepath, "r") as f:
        r = csv.DictReader(f, delimiter="\t", quotechar="'")
        for line in r:
            result[line[id_col]] = line[value_col]
    if value_fun is not None:
        for k, v in result.items():
            result[k] = value_fun(v)
    return result


def write_dict(features, filepath, id_col="id", value_col="index"):
    """write an id-index map into a file."""

    with open(filepath, "wt") as f:
        f.write(id_col + "\t" + value_col + "\n")
        for k, v in features.items():
            f.write(k + "\t" + str(v) + "\n")


def read_obj(filepath):
    """read a pickled object"""

    with open(filepath, "rb") as f:
        result = pickle.load(f)
    return result


def write_obj(obj, filepath):
    """read a pickled object"""

    with open(filepath, "wb") as f:
        pickle.dump(obj, f)


def write_matrix(data, ids, filepath, digits=5):
    """write an embedding into a tsv file

    Arguments:
        embedding    two-dimensional numpy array
        ids          dict mapping document ids to row indeces in embedding
        filepath     path to output file
    """

    n_dimensions = data.shape[1]
    with open(filepath, "wt") as f:
        temp = [None]*(n_dimensions+1)
        temp[0] = "id"
        for i in range(n_dimensions):
            temp[i+1] = "X" + str((1+i))
        f.write("\t".join(temp) + "\n")
        for k, v in ids.items():
            temp = [None]*(n_dimensions+1)
            temp[0] = k
            try:
                vdata = data[v].toarray()[0]
            except AttributeError:
                vdata = data[v]
            for i in range(n_dimensions):
                temp[i+1] = str(round(vdata[i], digits))
            f.write(("\t".join(temp)) + "\n")


def yaml_document(stream):
    """generator to read one yaml document at a time from a stream"""

    def parse_doc(d):
        doc = yaml.load("".join(d))
        doc_id = list(doc.keys())[0]
        return doc_id, doc[doc_id]

    data = []
    for line in stream:
        if line.startswith(" ") or line.startswith("\t"):
            data.append(line)
        elif len(data) == 0:
            data.append(line)
        else:
            yield parse_doc(data)
            data = [line]
    if len(data) > 0:
        yield parse_doc(data)

