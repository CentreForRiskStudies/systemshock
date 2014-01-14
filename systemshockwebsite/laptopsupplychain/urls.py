__author__ = 'Simon Ruffle'

from django.conf.urls import patterns, include, url
from laptopsupplychain import LaptopSupplyChainPage

urlpatterns = patterns('',
    url(r'^$', LaptopSupplyChainPage.as_view()),
)

