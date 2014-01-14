__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from locations import locations_list, locations_view, LocationsList, LocationsView

urlpatterns = patterns('',

    url(r'^$', locations_list, name='list'),   #locations list
    url(r'^(?P<ix>\d+)$', locations_view, name='view'), #view one location by id
    #url(r'^(?P<ix>\d+)/edit$', 'locations_edit', name='edit'),  #edit one location by id

    url(r'^list/$', LocationsList.as_view()),   #locations list using generic views

    url(r'^view/(?P<ix>\d+)$', LocationsView.as_view()),   #locations list using generic views
)
