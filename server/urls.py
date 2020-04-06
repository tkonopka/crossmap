"""
crossmap_server URL Configuration
"""

from django.urls import path
from . import views


urlpatterns = [
    path('add/', views.add, name='add'),
    path('document/', views.document, name='document'),
    path('datasets/', views.datasets, name='datasets'),
    path('decompose/', views.decompose, name='decompose'),
    path('diffuse/', views.diffuse, name='diffuse'),
    path('search/', views.search, name='search'),
]
