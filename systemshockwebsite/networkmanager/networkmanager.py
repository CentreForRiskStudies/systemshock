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

            # create a structure that will be sent to the web page graph/map viewer
            geonetworkviewerstructure = {}
            geonetworkviewerstructure['startup'] = {}

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

            markers = False
            try:
                if request.REQUEST['markers'] == 'True':
                    markers = True
            except:
                pass
            geonetworkviewerstructure['startup']['markers'] = markers

            shock = False
            try:
                if request.REQUEST['shock'] == 'True':
                    shock = True
            except:
                pass
            geonetworkviewerstructure['startup']['shock'] = shock

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

            # get network metrics - by default for the first layer in the network if multiple layers
            geonetworkviewerstructure['metrics'] = n.getMetrics()

            freezescenario = Freeze()
            viewer = Viewer()

            if self.page_context['ix'] == '6':
                # run Ben's supply chain model
                supplychainmodel = SupplyChain(None)
                supplychainmodel.run_model(n)
                #n.exportGexf('c:\\inetpub\\wwwroot\\networksessions\\pomegranite2.gexf')
                supplychainmodel.get_results()
                geonetworkviewerstructure['jsonGraph'] = supplychainmodel.json
            else:
                # simple viewer only
                viewermodel = ModellingBase(viewer)
                viewermodel.run_model(n)
                viewermodel.get_results()
                geonetworkviewerstructure['jsonGraph'] = viewermodel.json

            # run freeze model over supply chain - applies footprint and passes output in the JSON
            #supplychainmodel = SupplyChain(freezescenario)
            #supplychainmodel.get_run(self.page_context['ix'])
            #supplychainmodel.run_model(n)
            #supplychainmodel.get_results()
            #geonetworkviewerstructure['jsonGraph'] = supplychainmodel.json



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

            # pass the data to the geonetwork viewer template tag
            geonetworkviewerstructure['uniqueid'] = 1  # allows multiple viewers on same page
            self.page_context['geonetworkviewer1'] = geonetworkviewerstructure


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

