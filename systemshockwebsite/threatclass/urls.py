__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from threatclass import ThreatclassView

urlpatterns = patterns('',
    url(r'^$', ThreatclassView.as_view()),

)

