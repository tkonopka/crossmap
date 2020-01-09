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
    def wrapped(request, *args, **kw):
        if request.method == "OPTIONS":
            raw = ""
        elif request.method != "POST":
            raw = "Use POST. For curl, set --request POST\n"
        else:
            raw = dumps(f(request, *args, **kw))
        result = HttpResponse(raw)
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


def process_search_decompose(request, process_function):
    """handle search and decomposition"""

    doc = parse_request(request)
    dataset = doc["dataset"]
    result = process_function(doc, dataset=dataset, n=doc["n"],
                              diffusion=doc["diffusion"], query_name="query")
    targets = result["targets"]
    target_titles = crossmap.db.get_titles(dataset, ids=targets)
    result["titles"] = [target_titles[_] for _ in targets]
    return result


@access_http_response
def search(request):
    """process an http request to map a document onto nearest targets"""
    return process_search_decompose(request, crossmap.search)


@access_http_response
def decompose(request):
    """process an http request to decompose a document into basis"""
    return process_search_decompose(request, crossmap.decompose)


@access_http_response
def diffuse(request):
    """process an http request to find features a document diffuses into"""

    doc = parse_request(request)
    return crossmap.diffuse(doc, diffusion=doc["diffusion"])


@access_http_response
def datasets(request):
    """extract summary of available datasets and their sizes

    :param request: this is passed, but is not used
    :return: http response listing all available datasets
    """

    result = []
    size = crossmap.db.dataset_size
    for dataset in crossmap.db.datasets:
        result.append(dict(label=dataset, size=size(dataset)))
    return dict(datasets=result)


@access_http_response
def add(request):
    """add a new data item into the db

    :param request:
    :return: dictionary with success status of add
    """

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
    if doc["data"] == "" and doc["aux_pos"] == "":
        return dict(dataset=dataset, idx=[])
    idx = crossmap.add(dataset, doc, id, metadata=metadata)
    return dict(dataset=dataset, idx=idx)

