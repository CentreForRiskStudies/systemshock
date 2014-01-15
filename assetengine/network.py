__author__ = 'Simon Ruffle'

from django.db import models
from django.db import transaction
import networkx as nx
#from django.db.models import get_model
from networkx.readwrite import json_graph
import json
#from assetengine.models import Network as network_table
#from assetengine.models import Node as node_table
#from assetengine.models import NetworkLayer as layer_table
#from assetengine.models import Layer
#from assetengine.models import GetedgesBetweenLayers as edge_view
from assetengine.models import City, Country
from datetime import datetime
import ast
from django.db.models.loading import cache

class NetworkModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    typecode = models.CharField(max_length=10)
    timeunits = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    #collaboratorid = models.ForeignKey(Collaborator, null=True, db_column='collaboratorid', blank=True)

    class Meta:
        db_table = u'asset_engine\".\"network'

    def __unicode__(self):
        return self.name

class LayerModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    schema = models.CharField(max_length=50, blank=True)
    nodetablename = models.CharField(max_length=50, blank=True)
    edgetablename = models.CharField(max_length=50, blank=True)
    graphfilename = models.CharField(max_length=255, blank=True)
    typecode = models.CharField(max_length=50, blank=True)
    assetclasscode = models.CharField(max_length=10)
    isdirected = models.CharField(max_length=1)

    nodefilter = models.CharField(max_length=255, blank=True)
    edgefilter = models.CharField(max_length=255, blank=True)

    geobasetablename = models.CharField(max_length=100, blank=True)
    geobaseidcolumnname = models.CharField(max_length=255, blank=True)
    geobasegeomcolumnname = models.CharField(max_length=255, blank=True)
    geobasenamecolumnname = models.CharField(max_length=100, blank=True)

    tier = models.IntegerField(null=True, blank=True)

    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'asset_engine\".\"layer'

    def __unicode__(self):
        return self.name

class NetworkLayerModel(models.Model):
    id = models.AutoField(primary_key=True)
    networkid = models.ForeignKey(NetworkModel, db_column='networkid')
    layerid = models.ForeignKey(LayerModel, db_column='layerid')
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"networklayer'


class Network(object):

    def __init__(self):
        self.layergraphs = [] # networkx graphs for each layer
        self.layers = [] # database layers
        self.layeridlist = []
        self.statusMessage = ''
        self.aborted = False
        self.graphmodels = None  # underlying model-set to allow access to the underlying database tables
        self.networkobject = None # underlying record in the network table

    def abort(self, message):
        self.statusMessage = message
        self.aborted = True

    def WKTtoGeoJSON(self, wkt):
        import re
        try:
            geomtype = re.findall(r"[A-Za-z]+", wkt)[0]
            coordlist = [float(x) for x in re.findall(r"[\d+-.]+", wkt)]
            # TODO note this cannot yet deal with comma separated coordinate lists as found in LINESTRING etc
            geoJSON = {"type": geomtype, "coordinates": coordlist}    # this is GeoJSON format
        except:
            geoJSON = None
        return geoJSON

    # import a network from a gexf file

    def importGexf(self, url ):

        # TODO once files are stored in a standard upload directory this will need to be changed
        import platform
        if platform.system() == 'Windows':
            PATH = 'c:\\inetpub\\wwwroot\\pydev\\systemshock\\modellingengine\\fincat\\parameters\\'
        else:
            PATH = '/var/lib/geonode/src/GeoNodePy/geonode/modellingengine/fincat/parameters/'

        G = nx.read_gexf(PATH + url)

        # ensure the nodes are labelled with integers starting from 0
        # TODO might need to start from current number of nodes in G
        G = nx.convert_node_labels_to_integers(G, first_label=0)

        for node in G.nodes(data=True):
            nodeid = node[0] #node array index 0 is the node id, index 1 is the attribute list
            attributes = node[1]
            if 'wkt' in attributes:
                attributes['geometry'] = self.WKTtoGeoJSON(attributes['wkt'])

        self.layergraphs.append(G)  # add the new layer graph to the overall network
        return True

    def exportGexf(self, url):
        # join together all layers in the network
        H = nx.DiGraph()
        for G in self.layergraphs:
            H = nx.disjoint_union(G, H)
        nx.write_gexf(H, url)

    # load a network by id from the database into NetworkX
    def load(self, id, params={}):

        self.statusMessage = ''

        try:
            self.networkobject = NetworkModel.objects.get(pk=id)
        except:
            self.statusMessage = 'Cannot find network id ' + str(id)
            return False

        self.layers = NetworkLayerModel.objects.filter(networkid=id)
        if len(self.layers) > 0:
            for layer in self.layers:  # get each layer in the network
                nodetablename = layer.layerid.nodetablename
                edgetablename = layer.layerid.edgetablename
                schema = layer.layerid.schema
                typecode = layer.layerid.typecode
                graphfilename = layer.layerid.graphfilename
                node_filter = layer.layerid.nodefilter
                edge_filter = layer.layerid.edgefilter

                if schema is None:
                    schema = 'asset_engine'

                if nodetablename is not None:
                    # graph is to be read from database. Decide which database model-set to use
                    # based on the typecode column value in the layers table
                    specialtype = False
                    if typecode == 'supplychain':
                        self.graphmodels = SupplyChain(schema, nodetablename, schema, edgetablename, params)
                        G = nx.DiGraph()
                        specialtype = True
                    if typecode == 'citybase':
                        self.graphmodels = CityBase(schema, nodetablename, schema, edgetablename, params)
                        G = nx.DiGraph()
                        specialtype = True
                    if not specialtype:
                        self.graphmodels = GraphBase(schema, nodetablename, schema, edgetablename, params)
                        G = nx.DiGraph()

                    nodes = None
                    edges = None
                    if self.graphmodels.Nodes is not None:
                        nodes = self.graphmodels.Nodes.objects.all()
                    if self.graphmodels.Edges is not None:
                        edges = self.graphmodels.Edges.objects.all()

                    if node_filter is not None:
                        nodes = nodes.filter(**ast.literal_eval(node_filter))

                    numnodes = 0

                    try:
                        # check we can load the graph from the database
                        if nodes is not None:
                            numnodes = len(nodes)
                        if edges is not None:
                            numedges = len(edges)
                    except Exception, e:
                        self.statusMessage = e.message
                        return False

                    # create the nodes in graph
                    if numnodes > 0:
                        for node in nodes:
                            G.add_node(node.guid)

                            # iterate through all the fields in the node model and copy into the graph
                            for field in node._meta.fields:
                                if field.name not in ['id', 'the_geom', 'ownerid', 'lastupdatebyid', 'lastupdate', 'locationwkt', ]:
                                    fieldvalue = getattr(node, field.name)
                                    if field.get_internal_type() == 'ForeignKey':
                                        G.node[node.guid][field.name] = unicode(fieldvalue)     # by passing through unicode we flatten out any objects
                                                                                                # so we are sure they will serialise OK
                                                                                                # do we really need to do this?
                                    else:
                                        if fieldvalue is not None:
                                            G.node[node.guid][field.name] = fieldvalue

                            # treat geometry differently
                            G.node[node.guid]['geometry'] = self.WKTtoGeoJSON(node.locationwkt)

                            # add label
                            G.node[node.guid]['label'] = node.guid

                        # Now create the edges
                        if edges is not None:
                            for edge in edges:
                                # weight
                                weight = edge.weight
                                if weight is None:
                                    weight = 0

                                # distance
                                distance = edge.distance
                                if distance is None:
                                    distance = 0

                                G.add_edge(edge.startnodeguid, edge.endnodeguid, weight=weight, distance=distance, guid=edge.guid, ) # d3 needs value attribute equal to weight

                    else:
                        #self.statusMessage = 'no nodes found in the layers of the network'
                        #return -1
                        pass

                    self.layergraphs.append(G)  # add the new layer graph to the overall network

                else:
                    if graphfilename != '':
                        # GEXF file based graph, so load from disc
                        status = self.importGexf(graphfilename)
                        if not status:
                            return False
                    else:
                        self.statusMessage = 'could not find a valid layer definition'
                        return False
        else:
            self.statusMessage = 'no layers found in the network (poss invalid network id)'
            return False

        # set up default styles on nodes and links
        self.setStyles()

        return True

    def makePopup(self):
        for G in self.layergraphs:
            # Set up a simple default html popup for each node with the basic attributes
            for node in G.nodes(data=True):
                # when data=True we get the attributes of the node that we must unpack from an array
                guid = node[0]
                attributes = node[1]
                attributes['popup'] = '<div class="n">Node ' + str(guid) + '</div>'
                #if 'label' in attributes:
                #    attributes['popup'] += '<div class="p">' + unicode(attributes['label']) + '</div>'
                if 'name' in attributes:
                    attributes['popup'] += '<div class="a">' + unicode(attributes['name']) + '</div>'
                if 'countrycode' in attributes:
                    attributes['popup'] += '<div class="t">' + unicode(attributes['countrycode']) + '</div>'
                if 'citycode' in attributes:
                    attributes['popup'] += '<div class="c">' + unicode(attributes['citycode']) + '</div>'

                # append the in/out edge count
                attributes['popup'] += '<div class="e">Edges in: ' + unicode(G.in_degree(guid)) + ' out: ' + unicode(G.out_degree(guid)) + '</div>'

    def getMetrics(self, layerid=0):
        # get some overall network metrics
        undirectedG = self.layergraphs[layerid].to_undirected()
        metrics = {}

        try:  # must be connected
            metrics['diameter'] = nx.diameter(undirectedG)
            metrics['radius'] = nx.radius(undirectedG)
            metrics['average_clustering'] = round(nx.average_clustering(undirectedG),3)
            metrics['transitivity'] = round(nx.transitivity(undirectedG),3)
            metrics['number_connected_components'] = nx.number_connected_components(undirectedG)

            import operator
            betweenness_centrality = nx.betweenness_centrality(self.layergraphs[layerid])
            metrics['betweenness_centrality'] = sorted(betweenness_centrality.iteritems(),key=operator.itemgetter(1),reverse=True)[0][0] # find node with largest betweenness centrality

            H = nx.connected_component_subgraphs(undirectedG)[0] # largest connected component
            metrics['number_of_nodes'] = len(H.nodes())
        except:
            pass

        return metrics

    def setStyles(self, default=0):
        # in the absence of any other node and link style this will set up the
        # style attributes on node and links and set to a default value
        # also adds a layer id

        increment = 0

        for G in self.layergraphs:
            for node in G.nodes(data=True):
                # when data=True we get the attributes of the node that we must unpack from an array
                attributes = node[1]
                attributes['nodestyle'] = default
                attributes['layer'] = increment

            for edge in G.edges(data=True):
                attributes = edge[2]
                attributes['linkstyle'] = default
                attributes['layer'] = increment

            increment += 1

    def minimise(self, allowed_attributes = []):
        # use prior to a get_json, to strip out all attributes of the network that do not need to be sent in the JSON string to the client
        for G in self.layergraphs:
            for node in G.nodes(data=True):
                attributes = node[1]
                for deleteme, value in attributes.items():
                    if deleteme not in ['geometry', 'popup', 'nodestyle', 'layer', ] + allowed_attributes:
                        del(attributes[deleteme])

    def get_json(self):

        # join together all layers in the network
        H = nx.DiGraph()
        for G in self.layergraphs:
            H = nx.disjoint_union(G, H)

        data = json_graph.node_link_data(H)
        return json.dumps(data)

    def save(self, name, userid):

        # save the current network G into the database, with the given name,
        # creating a new network and returning the network id

        id = 0
        self.statusMessage = ''
        self.aborted = False

        new_network = NetworkModel()
        new_network.name = name
        new_network.lastupdate = datetime.now()
        new_network.lastupdatebyid = userid
        new_network.ownerid = userid

        with transaction.commit_manually():

            # create a new network record
            try:
                new_network.save()
                id = new_network.id
            except BaseException, e:
                self.abort(unicode(e))

            # create layer records
            if not self.aborted:
                pass

            # create node records
            if not self.aborted:
                pass

            # create edge records
            if not self.aborted:
                pass

            if self.aborted:
                transaction.rollback()
                self.statusMessage += ' / rollback'
            else:
                transaction.commit()


        # return the id of the network that just got created in the database
        # if zero look in self.statusMessage for error message
        return id


    def deleteNetwork(self, networkid, userid):

        # delete the network with id networkid. Deletes all owned layers, nodes and edges. If userid > 0, then that userid must be the owner of all elements to be deleted

        self.statusMessage = ''
        self.aborted = False

        try:
            network = NetworkModel.objects.get(pk=networkid)
        except BaseException, e:
            self.abort(e)

        if not self.aborted:
            with transaction.commit_manually():

                # delete the network record
                if userid > 0 and network.ownerid != userid:
                    self.abort('cannot delete, user does not own network id ' + unicode(networkid))

                if not self.aborted:
                    try:
                        network.delete()
                        self.statusMessage += "deleted network id " + unicode(networkid) + " "

                    except BaseException, e:
                        self.abort(unicode(e))
                # end of delete the network record

                # finish; either rollback or commit
                if self.aborted:
                    transaction.rollback()
                    self.statusMessage += ' / rollback'
                else:
                    transaction.commit()

        # return the status of the operation
        # if False look in self.statusMessage for error message
        # if True look in self.statusMessage for list of child elements deleted
        return not self.aborted


from django.db import models


class GraphBaseAbstract(object):
    # Dynamic class Factory for graph classes.
    # Allows node and edge models to be mapped dynamically to tables and columns at runtime.
    # This gets called by the constructor of this class
    def initNodeTable(self, node_schema, node_tablename, params={}):
        class NodeTable(models.Model):

            # columns common to all node tables
            id = models.IntegerField(primary_key=True)
            guid = models.CharField(max_length=10, unique=True)
            name = models.CharField(max_length=255, blank=True)
            description = models.TextField(blank=True)
            locationwkt = models.CharField(max_length=255, blank=True)
            #the_geom = models.TextField(blank=True,null=True) # This field type is a guess.
            countrycode = models.ForeignKey(Country, verbose_name='Country', to_field='iso3', db_column='countrycode')
            place = models.CharField(max_length=255, blank=True)
            url = models.CharField(max_length=255, blank=True)
            image1id = models.IntegerField(null=True, blank=True)
            lastupdate = models.DateTimeField(null=True, blank=True)
            lastupdatebyid = models.IntegerField(null=True, blank=True)
            ownerid = models.IntegerField(null=True, blank=True)

            class Meta:
                abstract = True

        return NodeTable

    def initEdgeTable(self, edge_schema, edge_tablename, params={}):
        class EdgeTable(models.Model):
            id = models.IntegerField(primary_key=True)
            guid = models.CharField(max_length=10)
            name = models.CharField(max_length=100, blank=True)
            weight = models.FloatField(null=True, blank=True)
            distance = models.FloatField(null=True, blank=True)
            description = models.TextField(blank=True)
            startnodeguid = models.CharField(max_length=10)
            endnodeguid = models.CharField(max_length=10)
            pathwkt = models.TextField(blank=True)
            #the_geom = models.TextField(blank=True) # This field type is a guess.
            #lastupdate = models.DateTimeField(null=True, blank=True)
            #lastupdatebyid = models.IntegerField(null=True, blank=True)
            #ownerid = models.IntegerField(null=True, blank=True)

            class Meta:
                abstract = True
        return EdgeTable

    def __init__(self, node_schema, node_tablename, edge_schema, edge_tablename, params):
        self.Nodes = None  # the underlying dynamic node table can be accessed through this model
        self.Edges = None  # the underlying dynamic edge table can be accessed through this model
        if node_tablename is not None:
            self.Nodes = self.initNodeTable(node_schema, node_tablename, params) # use the class factory to create a class for the node table
        if edge_tablename is not None:
            self.Edges = self.initEdgeTable(edge_schema, edge_tablename, params) # use the class factory to create a class for the edge table


class GraphBase(GraphBaseAbstract):

    def initBaseNodeTable(self, node_schema, node_tablename, params={}):
        if 'basenodetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['basenodetable']    # clear the model cache
        NodeModel = GraphBaseAbstract.initNodeTable(self, node_schema, node_tablename, params)

        class BaseNodeTable(NodeModel):

            class Meta(NodeModel.Meta):
                db_table = u'' + node_schema + '\".\"' + node_tablename
                managed = False

        return BaseNodeTable

    def initBaseEdgeTable(self, edge_schema, edge_tablename, params={}):
        if 'baseedgetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['baseedgetable']    # clear the model cache
        EdgeModel = GraphBaseAbstract.initEdgeTable(self, edge_schema, edge_tablename, params)

        class BaseEdgeTable(EdgeModel):

            class Meta(EdgeModel.Meta):
                db_table = u'' + edge_schema + '\".\"' + edge_tablename
                managed = False

        return BaseEdgeTable


    def __init__(self, node_schema, node_tablename, edge_schema, edge_tablename, params):
        self.Nodes = None
        self.Edges = None
        if node_tablename is not None:
            self.Nodes = self.initBaseNodeTable(node_schema, node_tablename, params) # use the class factory to create a class for the node table
        if edge_tablename is not None:
            self.Edges = self.initBaseEdgeTable(edge_schema, edge_tablename, params) # use the class factory to create a class for the edge table


class SupplyChain(GraphBaseAbstract):

    def initSupplyChainNodeTable(self, node_schema, node_tablename, params={}):
        if 'supplychainnodetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['supplychainnodetable']    # clear the model cache
        NodeModel = GraphBaseAbstract.initNodeTable(self, node_schema, node_tablename, params)

        class SupplyChainNodeTable(NodeModel):
            boundaryid = models.IntegerField(null=True, blank=True)
            organisation = models.CharField(max_length=255, blank=True)
            typecode = models.CharField(max_length=10, blank=True)
            activity = models.CharField(max_length=255, blank=True)
            tier = models.IntegerField(null=True, blank=True)

            class Meta(NodeModel.Meta):
                db_table = u'' + node_schema + '\".\"' + node_tablename
                managed = False

        return SupplyChainNodeTable

    def initSupplyChainEdgeTable(self, edge_schema, edge_tablename, params={}):
        if 'supplychainedgetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['supplychainedgetable']    # clear the model cache
        EdgeModel = GraphBaseAbstract.initEdgeTable(self, edge_schema, edge_tablename, params)

        class SupplyChainEdgeTable(EdgeModel):

            pass

            class Meta(EdgeModel.Meta):
                db_table = u'' + edge_schema + '\".\"' + edge_tablename
                managed = False

        return SupplyChainEdgeTable


    def __init__(self, node_schema, node_tablename, edge_schema, edge_tablename, params):

        self.Nodes = None
        self.Edges = None
        self.Products = None

        if node_tablename is not None:
            self.Nodes = self.initSupplyChainNodeTable(node_schema, node_tablename, params) # use the class factory to create a class for the node table
        if edge_tablename is not None:
            self.Edges = self.initSupplyChainEdgeTable(edge_schema, edge_tablename, params) # use the class factory to create a class for the edge table


class CityBase(GraphBaseAbstract):

    def initCityBaseNodeTable(self, node_schema, node_tablename, params={}):
        if 'citybasenodetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['citybasenodetable']    # clear the model cache
        NodeModel = GraphBaseAbstract.initNodeTable(self, node_schema, node_tablename, params)

        class CityBaseNodeTable(NodeModel):

            megacity = models.CharField(max_length=1, blank=True)
            capitalcity = models.CharField(max_length=1, blank=True)
            toptencitiesbypopulation = models.IntegerField()
            populationcitiesover750000_2015 = models.IntegerField(db_column='2015populationcitiesover750000')
            gdp2012 = models.FloatField()


            class Meta(NodeModel.Meta):
                db_table = u'' + node_schema + '\".\"' + node_tablename
                managed = False

        return CityBaseNodeTable

    def initCityBaseEdgeTable(self, edge_schema, edge_tablename, params={}):
        if 'citybaseedgetable' in cache.app_models['assetengine']:
            del cache.app_models['assetengine']['citybaseedgetable']    # clear the model cache
        EdgeModel = GraphBaseAbstract.initEdgeTable(self, edge_schema, edge_tablename, params)

        class CityBaseEdgeTable(EdgeModel):

            pass

            class Meta(EdgeModel.Meta):
                db_table = u'' + edge_schema + '\".\"' + edge_tablename
                managed = False

        return CityBaseEdgeTable


    def __init__(self, node_schema, node_tablename, edge_schema, edge_tablename, params):

        self.Nodes = None
        self.Edges = None
        self.Products = None

        if node_tablename is not None:
            self.Nodes = self.initCityBaseNodeTable(node_schema, node_tablename, params) # use the class factory to create a class for the node table
        if edge_tablename is not None:
            self.Edges = self.initCityBaseEdgeTable(edge_schema, edge_tablename, params) # use the class factory to create a class for the edge table