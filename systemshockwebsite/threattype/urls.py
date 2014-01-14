__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from threattype import ThreattypeView

urlpatterns = patterns('',
    url(r'^$', ThreattypeView.as_view()),



)

