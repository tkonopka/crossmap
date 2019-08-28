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
    for k in ["data", "aux_pos", "aux_neg"]:
        doc[k] = []
        if k in data:
            doc[k] = data[k]
    n_targets = get_or_default(data, "n_targets", 1)
    n_docs = get_or_default(data, "n_docs", 2)
    return doc, n_targets, n_docs


def process_request(request, process_function):
    """"""
    if request.method != "POST":
        return HttpResponse("Use POST protocol. For curl, set --request POST\n")
    doc, n_targets, n_docs = parse_request(request)
    result = process_function(doc, n_targets, n_docs, "query")
    return HttpResponse(dumps(result))


def predict(request):
    """process an http request to map a document onto nearest targets"""
    return process_request(request, crossmap.predict)


def decompose(request):
    """process an http request to decompose a document into basis"""
    return process_request(request, crossmap.decompose)
