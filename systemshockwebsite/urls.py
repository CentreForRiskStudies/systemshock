from django.conf.urls import patterns, include, url
from django.conf import settings
from django.views.static import *

import locations.urls
import home.urls
import taxonomy.urls
import networkmanager.urls
import photologue.urls
import threatclass.urls
import threattype.urls
import page.urls
import fincatrun.urls
import fincatbankparameter.urls
import node.urls
import weblib.urls
import shockindexhome.urls
import laptopsupplychain.urls
from page.page import BasicPage  #to allow shortcuts to basic pages

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', home, name='home'),   #home page

    url(r'^$',include(home.urls.urlpatterns)),   #home page when domain name only supplied; home is a customised basic content page

    url(r'^home/(?P<editmode>.*)/$',include(home.urls.urlpatterns)), #home page as /home/edit/
    url(r'^home',include(home.urls.urlpatterns)), #home page as /home

    url(r'^page/(?P<ix>.*)/(?P<editmode>.*)/$', include(page.urls.urlpatterns)), # the basic content page, edit mode, must come first, must have trailing slash
    url(r'^page/(?P<ix>.*)$', include(page.urls.urlpatterns)), # the basic content page, view mode

    url(r'^contact',BasicPage.as_view(), {'ix' : '3'}),  #shortcut to basic page by a friendly url name

    url(r'^policy',BasicPage.as_view(), {'ix' : '16'}),  #shortcut to Strategy Forum page
    url(r'^networks',BasicPage.as_view(), {'ix' : '21'}),  #shortcut to Network Manager page

    url(r'^taxonomy/(?P<editmode>.*)/$',include(taxonomy.urls.urlpatterns)), #taxonomy page edit mode which is a customised basic content page
    url(r'^taxonomy',include(taxonomy.urls.urlpatterns)), #taxonomy page which is a customised basic content page

    url(r'^threatclass/(?P<ix>.*)/(?P<editmode>.*)/$', include(threatclass.urls.urlpatterns)), # edit mode, must come first, must have trailing slash
    url(r'^threatclass/(?P<ix>.*)$', include(threatclass.urls.urlpatterns)),

    url(r'^threattype/(?P<ix>.*)/(?P<editmode>.*)/$', include(threattype.urls.urlpatterns)), # edit mode, must come first, must have trailing slash
    url(r'^threattype/(?P<ix>.*)$', include(threattype.urls.urlpatterns)),

    #url(r'^location', 'systemshock.locations.locations.location', name='location'),
    url(r'^locations/', include(locations.urls.urlpatterns)),

    url(r'^laptopsupplychain/(?P<editmode>.*)/$',include(laptopsupplychain.urls.urlpatterns)), #
    url(r'^laptopsupplychain/',include(laptopsupplychain.urls.urlpatterns)), #supply chain page which is a customised basic content page

    url(r'^fincatrun/(?P<ix>.*)/(?P<editmode>.*)/$', include(fincatrun.urls.urlpatterns)), # edit mode, must come first, must have trailing slash
    url(r'^fincatrun/(?P<ix>.*)$', include(fincatrun.urls.urlpatterns)),

    url(r'^fincatbankparameter/(?P<ix>.*)/(?P<editmode>.*)/$', include(fincatbankparameter.urls.urlpatterns)), # edit mode, must come first, must have trailing slash
    url(r'^fincatbankparameter/(?P<ix>.*)$', include(fincatbankparameter.urls.urlpatterns)),

    url(r'^shockindexhome/(?P<ix>.*)/(?P<editmode>.*)/$', include(shockindexhome.urls.urlpatterns)), # edit mode, must come first, must have trailing slash
    url(r'^shockindexhome/(?P<ix>.*)$', include(shockindexhome.urls.urlpatterns)),

    url(r'^networkmanager/(?P<ix>.*)/$',include(networkmanager.urls.urlpatterns)), #
    url(r'^networkmanager/',include(networkmanager.urls.urlpatterns)), #network manager page which is a customised basic content page


    url(r'^node/(?P<ix>.*)/(?P<editmode>.*)/$', include(node.urls.urlpatterns)), # the node page, edit mode, must come first, must have trailing slash
    url(r'^node/(?P<ix>.*)$', include(node.urls.urlpatterns)), # the node page, view mode

    url(r'^getdocument/(?P<ix>.*)$', include(weblib.urls.urlpatterns)), # the node page, view mode

    # url(r'^systemshock/', include('systemshock.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(r'^mediastore/(?P<path>.*)$','django.views.static.serve',{'document_root':settings.MEDIA_ROOT}),

    #photologue
    url(r'^photologue/', include('photologue.urls')),

    #comments framework
    url(r'^comments/', include('django.contrib.comments.urls')),

    # user login
    url (r'^login/?$', 'django.contrib.auth.views.login',{'template_name':'syshock_login.html'}),

    url (r'^logout/?$', 'django.contrib.auth.views.logout',{'template_name':'syshock_logout.html'}),


)
