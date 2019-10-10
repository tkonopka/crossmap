"""
crossmap_server URL Configuration
"""

from django.urls import path
from . import views


urlpatterns = [
    path('search/', views.search, name='search'),
    path('decompose/', views.decompose, name='decompose'),
    path('datasets/', views.datasets, name='datasets'),
]
