"""
views for crossmap server
"""

from functools import wraps
from json import dumps, loads
from crossmap.crossmap import Crossmap
from os import environ
from django.http import HttpResponse


# load the crossmap object based on configuration saved in an OS variable
config_path = environ.get('DJANGO_CROSSMAP_CONFIG_PATH')
crossmap = Crossmap(config_path)
crossmap.load()


def get_or_default(data, k, default=None):
    if k in data:
        return data[k]
    return default


def access_http_response(f):
    """decorator, ensures output of a function is turned into an HttpResponse"""

    @wraps(f)
    def wrapped(*args, **kw):
        raw = f(*args, **kw)
        result = HttpResponse(dumps(raw))
        result["Access-Control-Allow-Origin"] = "*"
        result["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        result["Access-Control-Max-Age"] = "1000"
        result["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type, Accept"
        return result

    return wrapped


def parse_request(request):
    """prepare curl data into parts suitable for search/decomposition

    :param request:
    :return: dictionary with arguments for search/decomposition
    """
    data = loads(request.body)
    doc = dict()
    for k in ["dataset", "data", "aux_pos", "aux_neg"]:
        doc[k] = data[k] if k in data else []
    doc["n"] = get_or_default(data, "n", 1)
    doc["paths"] = get_or_default(data, "paths", None)
    doc["diffusion"] = get_or_default(data, "diffusion", None)
    return doc


def parse_add_request(request):
    """prepare curl data into parts for add

    :param request:
    :return: dict with arguments for add()
    """

    data = loads(request.body)
    result = dict()
    for k in ["dataset", "id", "title",
              "data", "aux_pos", "aux_neg", "metadata"]:
        result[k] = data[k] if k in data else []
    if len(result["metadata"]) == 0:
        result["metadata"] = None
    else:
        result["metadata"] = dict(comment=result["metadata"])
    return result


def process_request(request, process_function):
    """abstract process function that handles search and decomposition"""
    if request.method == "OPTIONS":
        return ""
    if request.method != "POST":
        return "Use POST. For curl, set --request POST\n"
    doc = parse_request(request)
    dataset = doc["dataset"]
    result = process_function(doc, dataset=dataset, n=doc["n"],
                              paths=doc["paths"], diffusion=doc["diffusion"],
                              query_name="query")
    targets = result["targets"]
    target_titles = crossmap.db.get_titles(dataset, ids=targets)
    result["titles"] = [target_titles[_] for _ in targets]
    return result


def process_add_request(request):
    """handle calculations to add a new document into the db

    :param request:
    :return: dictionary with success status of add
    """

    if request.method == "OPTIONS":
        return ""
    if request.method != "POST":
        return "Use POST. For curl, set --request POST\n"
    doc = parse_add_request(request)
    dataset = str(doc.pop("dataset"))
    id = doc.pop("id")
    metadata = doc.pop("metadata")
    if id == "":
        id = dataset + ":0"
        if crossmap.db.validate_dataset_label(dataset) == 0:
            id = dataset + ":" + str(crossmap.db.dataset_size(dataset))
    if doc["title"] == "":
        doc["title"] = id
    if doc["data"] == "" and doc["data_pos"] == "":
        return dict(dataset=dataset, idx=[])
    idx = crossmap.add(dataset, doc, id, metadata=metadata)
    return dict(dataset=dataset, idx=idx)


@access_http_response
def search(request):
    """process an http request to map a document onto nearest targets"""
    return process_request(request, crossmap.search)


@access_http_response
def decompose(request):
    """process an http request to decompose a document into basis"""
    return process_request(request, crossmap.decompose)


@access_http_response
def datasets(request):
    """extract summary of available datasets and their sizes"""

    result = []
    size = crossmap.db.dataset_size
    for dataset in crossmap.db.datasets:
        result.append(dict(label=dataset, size=size(dataset)))
    return dict(datasets=result)


@access_http_response
def add(request):
    """add a new data item into the db"""

    return process_add_request(request)

