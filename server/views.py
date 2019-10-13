"""
views for crossmap server
"""

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


def parse_request(request):
    """prepare curl data into parts suitable for prediction/decomposition

    :param request:
    :return: three items, a dict with a document structure,
    an integer n_targets, an integer n_documents
    """
    data = loads(request.body)
    doc = dict()
    for k in ["dataset", "data", "aux_pos", "aux_neg"]:
        doc[k] = []
        if k in data:
            doc[k] = data[k]
    doc["n"] = get_or_default(data, "n", 1)
    doc["paths"] = get_or_default(data, "paths", None)
    doc["diffusion"] = get_or_default(data, "diffusion", None)
    return doc


def add_access(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Max-Age"] = "1000"
    response["Access-Control-Allow-Headers"] = "X-Requested-With, Content-Type, Accept"
    return response


def process_request(request, process_function):
    """abstract process function that handles prediction and decomposition"""
    if request.method == "OPTIONS":
        return add_access(HttpResponse(""))
    if request.method != "POST":
        return HttpResponse("Use POST. For curl, set --request POST\n")
    # perform core processing
    doc = parse_request(request)
    dataset = doc["dataset"]
    result = process_function(doc, dataset=dataset, n=doc["n"],
                              paths=doc["paths"], diffusion=doc["diffusion"],
                              query_name="query")
    targets = result["targets"]
    target_titles = crossmap.db.get_titles(dataset, ids=targets)
    result["titles"] = [target_titles[_] for _ in targets]
    return add_access(HttpResponse(dumps(result)))


def search(request):
    """process an http request to map a document onto nearest targets"""
    return process_request(request, crossmap.predict)


def decompose(request):
    """process an http request to decompose a document into basis"""
    return process_request(request, crossmap.decompose)


def datasets(request):
    """extract summary of available datasets and their sizes"""

    str(request)
    result = []
    size = crossmap.db.dataset_size
    for dataset in crossmap.db.datasets:
        result.append(dict(label=dataset, size=size(dataset)))
    return add_access(HttpResponse(dumps(dict(datasets=result))))

