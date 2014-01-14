__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from networkmanager import NetworkManagerPage

urlpatterns = patterns('',
    url(r'^$', NetworkManagerPage.as_view()),
)

