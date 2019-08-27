from crossmap.crossmap import Crossmap
from os import environ
from django.http import HttpResponse

# load the crossmap object based on configuration saved in an OS variable
config_path = environ.get('DJANGO_CROSSMAP_CONFIG_PATH')
crossmap = Crossmap(config_path)
crossmap.load()

def predict(request):
    return HttpResponse("In predict. "+str(crossmap.settings))


def decompose(request):
    return HttpResponse("In decompose.")

