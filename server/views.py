"""
views for crossmap server
"""

from functools import wraps
from json import dumps, loads
from crossmap.crossmap import Crossmap
from crossmap.settings import CrossmapSettings
from crossmap.vectors import sparse_to_dense
from os import environ
from urllib.parse import unquote
from django.http import HttpResponse
from logging import info
import yaml

# load the crossmap object based on configuration saved in an OS variable
config_path = environ.get('DJANGO_CROSSMAP_CONFIG_PATH')
settings = CrossmapSettings(config_path, require_data_files=False)
crossmap = Crossmap(settings)
crossmap.load()
info("database collections: "+str(crossmap.db._db.list_collection_names()))


def get_vector(dataset, item_id):
    db = crossmap.indexer.db
    result = db.get_data(dataset, ids=[item_id])
    return result[0]["data"]


def decr_by_query(a):
    return -a["query"]


def find_vector(item_id, dataset=None):
    """find an item in some unspecified dataset

    :param item_id: identifier for a data item
    :param dataset: label for a dataset. The function attempts to to find
        the item in this dataset first, but also checks other datasets as
        a fallback
    :return: csr vector for the item, or None if not found
    """

    db = crossmap.db
    if dataset is not None and db.has_id(dataset, item_id):
        return get_vector(dataset, item_id)
    for d in db.datasets.keys():
        if db.has_id(d, item_id):
            return get_vector(d, item_id)
    return None


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
    for k in ["dataset", "data_pos", "data_neg"]:
        doc[k] = data.get(k, [])
    doc["n"] = data.get("n", 1)
    for k in ["diffusion", "expected_id", "query_id"]:
        doc[k] = data.get(k, None)
    return doc


def parse_add_request(request):
    """prepare curl data into parts for add

    :param request:
    :return: dict with arguments for add()
    """

    data = loads(request.body)
    result = dict()
    for k in ["dataset", "id", "title",
              "data_pos", "data_neg", "metadata"]:
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
    db = crossmap.db

    # try to use data_pos as an item_id
    doc_input = doc
    item_id = doc["data_pos"]
    if len(item_id.split(" ")) == 1:
        for d in db.datasets.keys():
            if db.has_id(d, item_id):
                doc_input = db.get_document(d, item_id)

    # process the input
    result = process_function(doc_input, dataset=dataset, n=doc["n"],
                              diffusion=doc["diffusion"], query_name="query")
    targets = result["targets"]
    target_titles = crossmap.db.get_titles(dataset, ids=targets)
    result["titles"] = [target_titles[_] for _ in targets]
    result["dataset"] = dataset
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
    :return: dictionary with new integer ids (idx)
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
    if doc["data_pos"] == "":
        return dict(dataset=dataset, idx=[])
    idx = crossmap.add(dataset, doc, id, metadata=metadata)
    return dict(dataset=dataset, idx=idx)


@access_http_response
def document(request):
    """process an http request to map a document onto nearest targets"""
    data = loads(request.body)
    result = crossmap.db.get_document(unquote(data["dataset"]),
                                      unquote(data["id"]))
    return yaml.dump(result)


@access_http_response
def delta(request):
    """suggest features for user-driven learning

    :param request: object with data_pos, data_neg, expected_id
    :return: dictionary with top features, suggest_pos, suggest_neg
    """

    doc = parse_request(request)
    dataset = doc["dataset"]
    db = crossmap.db
    # process a query
    query_id = doc["query_id"]
    query_raw = find_vector(query_id, dataset)
    if query_raw is None:
        return {"error": "invalid item id: " + query_id}
    query_diffused = crossmap.diffuser.diffuse(query_raw, doc["diffusion"])
    diffused = sparse_to_dense(query_diffused)
    # get hits
    targets, _ = crossmap.indexer.suggest(diffused, dataset=dataset, n=doc["n"])
    # get feature vectors for the expected_id and top_hits
    expected_raw = find_vector(doc["expected_id"], dataset)
    if expected_raw is None:
        return {"error": "invalid item id: "+doc["expected_id"]}
    expected = sparse_to_dense(expected_raw)
    vectors = {
        "query": sparse_to_dense(query_raw),
        "diffused": diffused,
        "expected": expected,
        "error": expected-diffused
    }
    for i, hit_id in enumerate(targets):
        i_vector = sparse_to_dense(get_vector(dataset, hit_id))
        vectors["hit_"+str(i+1)] = i_vector
        vectors["delta_"+str(i+1)] = i_vector - expected
    inv_feature_map = crossmap.indexer.encoder.inv_feature_map
    result = []
    for i in range(len(inv_feature_map)):
        i_data = [abs(_[i]) for _ in vectors.values()]
        if sum(i_data) == 0:
            continue
        i_result = dict(feature=inv_feature_map[i])
        for vector_id, vector_values in vectors.items():
            i_result[vector_id] = vector_values[i]
        result.append(i_result)
    result = sorted(result, key=decr_by_query)
    return result
