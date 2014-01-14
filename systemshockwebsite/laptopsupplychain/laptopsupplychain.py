__author__ = 'Simon Ruffle'

from django.shortcuts import render
from django.db.models import get_model
from weblib.baseclasses.pagebase import Pagebase
from assetengine.network import Network
from django.forms import ModelForm
from weblib.models import Page
from django.http import HttpResponseRedirect
from datetime import datetime
import networkx as nx

template_dir = 'laptopsupplychain/templates/'

appname = 'weblib'
modelname = 'Page'

class PageFormEdit (ModelForm):
    class Meta:
        model = Page
        fields = ('name', 'subtitle', 'introtext', 'maintext',  )

class PageFormDisplay (ModelForm):
    class Meta:
        model = Page
        fields = ( 'introtext', 'maintext', )

class LaptopSupplyChainPage (Pagebase):

    template_name = template_dir + "laptopsupplychain.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            ###import json
            #import urllib2
            #urlStr = 'http://gemecd.org:8080/geoserver/gemecd/ows?service=WFS&version=1.0.0&request=GetFeature&typeName=gemecd:geoarchivelocations&maxFeatures=5000&outputFormat=json'
            #jsonStr = urllib2.urlopen(urlStr).read()  #pass this string to leaflet L.geoJson(geojsonFeature).addTo(map);
            ###jsonData = json.loads(jsonStr)  #only of you want to process the GeoJSON in Python

            ix = 15 # network manager page id
            self.page_context['ix'] = str(ix)

            tabmode = 'list'
            self.page_context['init_code'] = ''
            try:
                if request.REQUEST['tab'] == 'map':
                    tabmode='map'
                if request.REQUEST['tab'] == 'list':
                    tabmode='list'
                if request.REQUEST['tab'] == 'topo':
                    tabmode='map'
                    self.page_context['init_code'] += 'toggle();'
            except:
                pass
            self.page_context['tabmode'] = tabmode

            distrib = True
            try:
                if request.REQUEST['distrib'] == 'False':
                    distrib = False
                    self.page_context['init_code'] += 'toggleTminus1vis();'
            except:
                pass
            self.page_context['distrib'] = str(distrib)

            footprint = False
            try:
                if request.REQUEST['footprint'] == 'True':
                    footprint = True
                    self.page_context['init_code'] += 'footprintvisibility();'
            except:
                pass
            self.page_context['footprint'] = str(footprint)

            markers = False
            try:
                if request.REQUEST['markers'] == 'True':
                    markers = True
                    self.page_context['init_code'] += 'graph.markForDeletion();'
            except:
                pass
            self.page_context['markers'] = str(markers)

            shock = False
            try:
                if request.REQUEST['shock'] == 'True':
                    shock = True
                    self.page_context['init_code'] += 'remove_onclick();'
            except:
                pass
            self.page_context['shock'] = str(shock)


            displayiteration = 'final'
            try:
                if request.REQUEST['iter'] == 'start':
                    displayiteration = 'start'
            except:
                pass
            self.page_context['iter'] = displayiteration

            api = request.GET.get('api')
            if api is None or api == '' or api == 'leaflet':
                api = 'leaflet'
            else:
                api = 'OL'
            self.page_context['api'] = api

            stage = 1
            try:
                if request.REQUEST['stage']:
                    stage = int(request.REQUEST['stage'])
            except:
                pass
            self.page_context['stage'] = stage

            page_subtitle = 'unknown'
            # process what gets displayed in the text box and the functions of the next and previous buttons

            if stage == 1:
                #prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=0&tab=map">&laquo; previous</a>'
                prevbutton = ''
                nextbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=2&tab=topo&distrib=True">next &raquo;</a>'
                starttext = 'This is the supply chain of a fictional electronics company <i>Pomegranate</i> which is manufacturing and distributing a 4G tablet computer. The map is interactive: hold your cursor over a node to see its data. Use the top buttons to isolate different parts of the network - the Distribution network of completed products to their markets, and Suppliers in Tier 1 (assembly of principle components); Tier 2 (sub-components); Tier 3 (raw materials). '
                page_subtitle = '1. Supply Chain Geography of a Global Electronics Company'

            if stage == 2:
                prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=1&tab=map&distrib=True">&laquo; back</a>'
                nextbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=3&tab=map&footprint=True&distrib=True">next &raquo;</a>'
                starttext = 'Here we switch the view of the supply chain from geographical (plotted on a world map) to topological (a force-directed graph diagram of the network model). Note that the same data are retained - your cursor still brings up the same data in a pop-up. The force-directed graph can be dragged and manipulated to view interactivity of the network. Topology of a network shows process flow, choke points and dependencies.'
                page_subtitle = '2. Supply Chain Network Model'

            if stage == 3:
                prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=2&tab=topo&distrib=True">&laquo; back</a>'
                nextbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=4&tab=map&distrib=True&markers=True&footprint=True">next &raquo;</a>'
                starttext = 'Back on the geographical map, the supply chain process is now affected by a shock scenario from our <a href="/taxonomy">Threat Observatory</a>. In this example we show the footprint of an extreme cold winter event that might be expected about once a century, as documented in our <a href="/uploaded/documents/Freeze.pdf" target="_new">Freeze Threat Profile</a> working paper. Freezing conditions, with heavy snow and ice, are experienced for over 6 weeks.'
                page_subtitle = '3. Applying a Scenario Footprint'

            if stage == 4:
                prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=3&tab=map&footprint=True&distrib=True">&laquo; back</a>'
                nextbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=5&tab=topo&distrib=True&markers=True&footprint=True">next &raquo;</a>'
                starttext = 'The cold weather is so extreme it reduces manufacturing productivity, stops transport and suppresses consumer demand. A spatial query identifies the nodes of the network that lie within each intensity zone of the freeze event and assigns an intensity to each node. All of the nodes affected by the freeze event are highlighted by a blue diamond. '
                page_subtitle = '4. Identifying the Affected Nodes'

            if stage == 5:
                prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=4&tab=map&distrib=True&markers=True&footprint=True">&laquo; back</a>'
                nextbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=6&tab=topo&distrib=True&markers=True&footprint=True&shock=True">next &raquo;</a>'
                starttext = 'The nodes that are affected by the freeze event are identified by their position in the supply chain network model. Their performance is degraded depending on the intensity of the scenario that they experienced. For simplicity in this example the node is assumed to be rendered completely inactive.'
                page_subtitle = '5. Affected Nodes in the Supply Chain Model'

            if stage == 6:
                prevbutton = '<a href="/laptopsupplychain/' + self.page_context['ix'] + '?stage=5&tab=topo&distrib=True&markers=True&footprint=True">&laquo; back</a>'
                nextbutton = '<a href="/page/26">next &raquo;</a>'
                starttext = 'The nodes are disabled in the network. In graph theory it performs a k-cut operation where k=41, with an identity of co-location in the freeze footprint. Links to and from an inactive node are severed. The network functionality is extremely compromised. The network re-resolves but with extremely limited residual value function. A number of nodes are completely disconnected.'
                page_subtitle = '6. Shock the System'

            self.page_context['nextbutton'] = nextbutton
            self.page_context['prevbutton'] = prevbutton
            self.page_context['starttext'] = starttext


            n = Network()
            status = n.load(6)  #load a network from the asset engine database by its network id
            if not status:
                return self.showErrorPage(request, 'Error loading network : ' + n.statusMessage)
            # process the graph to set up the special attributes that are going to be sent to the client side javascript via JSON
            for node in n.layergraphs[0].nodes(data=True):

                # when data=True we get the attributes of the node that we must unpack from an array
                guid = node[0]
                attributes = node[1]

                # the node name attribute is used to form the pop up html
                attributes['name'] = '<div class="n">Node ' + attributes['guid'] + '</div><div class="t">Tier ' + str(attributes['tier']) + '</div><div class="a">' + attributes['activity'] + '</div><div class="p">' + attributes['name']  + '</div><div class="c">' + attributes['countrycode'] + '</div>'

                # append the in/out edge count to the node name
                attributes['name'] += '<div class="e">Edges in: ' + unicode(n.layergraphs[0].in_degree(guid)) + ' out: ' + unicode(n.layergraphs[0].out_degree(guid)) + '</div>'

                #get the tier of this node
                tier = attributes['tier']

                # find the edges that go out of this node
                out_edges = n.layergraphs[0].out_edges(guid)  # gets outward edges
                for edge in out_edges:
                    # create a tier attribute on the edge
                    n.layergraphs[0][edge[0]][edge[1]]['tier']=tier

            for edge in n.layergraphs[0].edges(data=True):
                n.layergraphs[0][edge[0]][edge[1]]['value'] = 1  # d3 needs this

            # get some overall network metrics
            undirectedG = n.layergraphs[0].to_undirected()
            self.page_context['diameter'] = nx.diameter(undirectedG)
            self.page_context['radius'] = nx.radius(undirectedG)
            self.page_context['average_clustering'] = round(nx.average_clustering(undirectedG),3)
            self.page_context['transitivity'] = round(nx.transitivity(undirectedG),3)
            self.page_context['number_connected_components'] = nx.number_connected_components(undirectedG)

            import operator
            betweenness_centrality = nx.betweenness_centrality(n.layergraphs[0])
            self.page_context['betweenness_centrality'] = sorted(betweenness_centrality.iteritems(),key=operator.itemgetter(1),reverse=True)[0][0][5:] # find node with largest betweenness centrality

            H = nx.connected_component_subgraphs(undirectedG)[0] # largest connected component
            self.page_context['number_of_nodes'] = len(H.nodes())

            # apply freeze footprint, assigning intensities to nodes in footprint
            from footprints.footprint import Footprint
            f = Footprint('freeze100', ['intensity'])
            f.apply('asset_engine.node', n.layergraphs[0])

            jsonGraphStr = n.get_json()

            # now we have the json string which has intensities for the footprint,
            # apply freeze footprint again but this time delete the nodes in the footprint
            f.apply('asset_engine.node', n.layergraphs[0], None, True)

            # get same overall network metrics now we have the post K-cut network
            undirectedG = n.layergraphs[0].to_undirected()
            self.page_context['average_clustering_K'] = round(nx.average_clustering(undirectedG),3)
            self.page_context['transitivity_K'] = round(nx.transitivity(undirectedG),3)
            self.page_context['number_connected_components_K'] = nx.number_connected_components(undirectedG)

            betweenness_centrality = nx.betweenness_centrality(n.layergraphs[0])
            self.page_context['betweenness_centrality_K'] = sorted(betweenness_centrality.iteritems(),key=operator.itemgetter(1),reverse=True)[0][0][5:] # find node with largest betweenness centrality

            H = nx.connected_component_subgraphs(undirectedG)[0] # largest connected component
            self.page_context['number_of_nodes_K'] = len(H.nodes())

            # load a network from its GEXF file
            # base bank network
            #n.importGexf('c:\\inetpub\\wwwroot\\pydev\\systemshock\\modellingengine\\fincat\\parameters\\countries.gexf')
            # initial capital ratio
            #n.importGexf('c:\\inetpub\\wwwroot\\pydev\\systemshock\\modellingengine\\fincat\\parameters\\initial.gexf')
            # final capital ratio
            #n.importGexf('c:\\inetpub\\wwwroot\\pydev\\systemshock\\modellingengine\\fincat\\parameters\\results.gexf')
            #jsonGraphStr = n._get_json()

            session_key = ''
            if request.session._session_key is None:
                request.session._get_or_create_session_key()  # note this returns the wrong key, so can't use the key until the page's next roundtrip
            else:
                session_key = request.session._session_key

            #if session_key != '':
            #    n.exportGexf('c:\\inetpub\\wwwroot\\networksessions\\' + session_key + '.gexf')

            current_object = Page.objects.get(pk=ix)
            page_title = current_object.name
            #page_subtitle = current_object.subtitle
            self.page_context['ix'] = ix
            self.page_context['page_title'] = page_title
            self.page_context['page_subtitle'] = page_subtitle

            # display
            pageFormDisplay = PageFormDisplay (instance=current_object)
            pagefields = self.createFormFieldStructure( pageFormDisplay, current_object )

            # using a class dictionary from Pagebase in weblib
            self.page_context['pageclass'] = 'networkmanager'
            self.page_context['tablesetup1'] = pagefields
            self.page_context['editlink'] = '/laptopsupplychain'
            self.page_context['current_object'] = current_object
            self.page_context['this_page'] = request.path
            self.page_context['jsonGraph'] = jsonGraphStr
            self.page_context['api'] = api
            #self.page_context['haiti'] = jsonStr

            ###############
            # POST
            ###############

            if request.method == 'POST':
                pageFormEdit = PageFormEdit(request.POST, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms
                if pageFormEdit.is_valid(): # All validation rules pass

                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    pageFormEdit.save()

                    return HttpResponseRedirect('/laptopsupplychain') # Redirect after successful POST to the non editing version
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

