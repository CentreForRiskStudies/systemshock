__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from weblib.views import GetDocument

urlpatterns = patterns('',
    url(r'^$', GetDocument.as_view()),

)

