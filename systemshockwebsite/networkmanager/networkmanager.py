__author__ = 'Simon Ruffle'

from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from assetengine.network import Network
from assetengine.models import Network as network_table
from django.forms import ModelForm
from weblib.models import Page
from django.http import HttpResponseRedirect
from datetime import datetime
import networkx as nx
from modellingengine.supplychain import SupplyChain
from modellingengine.modellingbase import ModellingBase
from threatengine.scenariobase import Freeze, Viewer
import ast

template_dir = 'networkmanager/templates/'

class PageFormEdit (ModelForm):
    class Meta:
        model = network_table
        fields = ('name', 'description', )

class PageFormDisplay (ModelForm):
    class Meta:
        model = network_table
        fields = ('name', 'description', )

class NetworkManagerPage (Pagebase):

    template_name = template_dir + "networkmanager.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            # create a structure that will be sent to the web page graph viewer
            geonetworkviewerstructure = {}
            geonetworkviewerstructure['startup'] = {}

            # create a structure that will be sent to the web page map viewer
            mapviewerstructure = {}
            mapviewerstructure['startup'] = {}

            tabmode = 'map'
            try:
                if request.REQUEST['tab'] == 'topo':
                    tabmode = 'topo'
            except:
                pass
            geonetworkviewerstructure['startup']['tabmode'] = str(tabmode).lower

            footprint = False
            try:
                if request.REQUEST['footprint'] == 'True':
                    footprint = True
            except:
                pass
            geonetworkviewerstructure['startup']['footprint'] = footprint
            mapviewerstructure['startup']['footprint'] = footprint

            markers = False
            try:
                if request.REQUEST['markers'] == 'True':
                    markers = True
            except:
                pass
            geonetworkviewerstructure['startup']['markers'] = markers
            mapviewerstructure['startup']['markers'] = markers

            shock = False
            try:
                if request.REQUEST['shock'] == 'True':
                    shock = True
            except:
                pass
            geonetworkviewerstructure['startup']['shock'] = shock
            mapviewerstructure['startup']['shock'] = shock

            n = Network()
            try:
                ix = int(self.page_context['ix'])
            except:
                return self.showErrorPage(request, 'Invalid network id')

            status = n.load(ix)  # load a network from the asset engine database by its network id

            if not status:
                return self.showErrorPage(request, 'Error loading network : ' + n.statusMessage)

            # make default popup
            n.makePopup()

            # create the list of nodes - may be more than one list depending on how many networks
            self.page_context['nodelistlist'] = []
            listganglist = ['graph1', 'map2']
            listviewerid = 1

            for index, graphmodels in enumerate(n.graphmodelslist):
                node_filter = n.layers[index].layerid.nodefilter
                nodequeryset = graphmodels.Nodes.objects.only('id','guid', 'image1','name', 'countrycode').all().order_by('name')
                if node_filter is not None:
                        nodequeryset = nodequeryset.filter(**ast.literal_eval(node_filter))
                fieldlist=\
                        [
                            [{'guid' :  { 'title' : 'GUID', 'type' : 'text', }}], # NB guid must be first for the ganged grid list templatetag to find it
                            [{'image1': {'title': 'Image', 'type' : 'WebLibPhoto', 'photosize' : 'admin_thumbnail'}}],
                            [{'name' :  { 'title' : 'Node name', 'type' : 'text', }}],
                            [{'countrycode' :  { 'title' : 'Country', 'type' : 'text', }}]
                       ]
                fieldstructure = {'entity': nodequeryset, 'targeturl': '/node/' + unicode(n.layeridlist[index]) +  '/',
                                  'fields': fieldlist, 'params': {'linkforeignkeys': False, 'ganglist': listganglist, 'viewerid': listviewerid} }
                self.page_context['nodelistlist'].append(fieldstructure)


            # set up the scenario
            freezescenario = Freeze()
            viewer = Viewer()

            if self.page_context['ix'] == '6':
                # run Ben's supply chain model
                supplychainmodel = SupplyChain(freezescenario)
                supplychainmodel.run_model(n, 0, 0, shock)
                #n.exportGexf('c:\\inetpub\\wwwroot\\networksessions\\pomegranite2.gexf')
                supplychainmodel.get_results()
                geonetworkviewerstructure['jsonGraph'] = supplychainmodel.json
                mapviewerstructure['geojson'] = supplychainmodel.geojson

            else:
                # simple viewer only
                viewermodel = ModellingBase(viewer)
                viewermodel.run_model(n)
                viewermodel.get_results()
                geonetworkviewerstructure['jsonGraph'] = viewermodel.json
                mapviewerstructure['geojson'] = viewermodel.geojson

            # run freeze model over supply chain - applies footprint and passes output in the JSON
            #supplychainmodel = SupplyChain(freezescenario)
            #supplychainmodel.get_run(self.page_context['ix'])
            #supplychainmodel.run_model(n)
            #supplychainmodel.get_results()
            #geonetworkviewerstructure['jsonGraph'] = supplychainmodel.json

            # get network metrics - by default for the first layer in the network if multiple layers
            geonetworkviewerstructure['metrics'] = n.getMetrics()

            current_object = n.networkobject
            page_title = current_object.name
            page_subtitle = current_object.description
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle

            # display network fields and editable form
            pageFormDisplay = PageFormDisplay(instance=current_object)
            pagefields = self.createFormFieldStructure(pageFormDisplay, current_object )

            # using a class dictionary from Pagebase in weblib
            self.page_context['pageclass'] = 'networkmanager'
            self.page_context['tablesetup1'] = pagefields
            self.page_context['editlink'] = '/networkmanager'
            self.page_context['current_object'] = current_object
            self.page_context['this_page'] = request.path

            # pass the data to the network viewer template tag
            geonetworkviewerstructure['ganglist'] = ['map2'] # connects graph viewer to map viewer
            geonetworkviewerstructure['uniqueid'] = 1  # allows multiple viewers on same page
            self.page_context['graphviewer1'] = geonetworkviewerstructure

            # pass the data to the map viewer template tag
            mapviewerstructure['ganglist'] = ['graph1'] # connects map viewer to graph viewer
            mapviewerstructure['uniqueid'] = 2  # allows multiple viewers on same page
            self.page_context['mapviewer2'] = mapviewerstructure

            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = PageFormEdit(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/networkmanager') # Redirect after successful POST to the non editing version
                else:
                    self.page_context['form'] = pageFormEdit

                    return render(request, self.template_name, self.page_context)  # Error - return just the form when there is an error - the template must not try and render anything outside the form because the contact data is not present


            ###############
            # GET
            ###############

            if request.method == 'GET':

                # edit form
                if self.page_context['editmode']:
                    pageFormEdit = PageFormEdit (instance=current_object, prefix="mainpageform") #prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit

                return render(request, self.template_name, self.page_context)

