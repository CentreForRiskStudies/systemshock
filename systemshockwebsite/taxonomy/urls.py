__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from taxonomy import TaxonomyPage

urlpatterns = patterns('',
    url(r'^$', TaxonomyPage.as_view()),
)

