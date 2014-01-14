__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from fincatrun import FinCatRunPage

urlpatterns = patterns('',
    url(r'^$', FinCatRunPage.as_view()),

)

