__author__ = 'Simon Ruffle'
import sys
from django.db.models import get_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

#from laptopsupplychaindemo import models
from datetime import datetime
from email.utils import parsedate_tz
import networkx as nx
#import matplotlib.pyplot as plt
#from networkx import graphviz_layout

# how to import black_rhino
# from black_rhino.src.environment import Environment
#e = Environment()

from networkx.readwrite import json_graph


class Command(BaseCommand):
    args = '<file_name>'
    help = 'imports an NRML file into the GEMECD database'

    def handle(self, *args, **options):
        for number_of_turns in args:
            #try:
            #    event = models.Event.objects.get(pk=int(event_id))
            #except models.Event.DoesNotExist:
            #    raise CommandError('Event "%s" does not exist' % poll_id)

            #            poll.opened = False
            #            poll.save()

            #            self.stdout.write('Successfully closed poll "%s"\n' % poll_id)
            #           poll.question='Standard Damage Scale xxx'
            #           poll.save()
            #attributename = 'name'
            #            self.stdout.write('Poll id ' + poll_id + ' = ' + poll.question)
            #self.stdout.write('Event id ' + event_id + ' = ' + getattr(event, attributename) + '\n')



            G = nx.DiGraph()

            #nodemodel = get_model('laptopsupplychaindemo', 'laptopnode')
            nodemodel = get_model('assetengine', 'node')
            nodes = nodemodel.objects.filter(layerid__lte=4) #quick and dirty way of getting the laptop footprint

            for node in nodes:
                G.add_node(node.guid)
                G.node[node.guid]['name'] = "Node " + unicode(node.guid) + " "  + unicode(node.country) + "/" + unicode(node.place) + ": " + unicode(node.activity) + ", tier " + unicode(int(node.layerid.id) - 1)
                G.node[node.guid]['tier'] = unicode(int(node.layerid.id) - 1)
                G.node[node.guid]['intensity'] = unicode(0)     # default intensity

                #parse WKT
                lon = 0
                lat = 0
                wkt = node.locationwkt
                wkt = wkt.replace('POINT' , '')
                wkt = wkt.replace('(' , '')
                wkt = wkt.replace(')' , '')
                wkt = " ".join(wkt.split()) #strip extra spaces
                wktArr = wkt.split(' ')

                try:
                    lon = float(wktArr[0])
                    lat = float(wktArr[1])
                except:
                    lon = 0
                    lat = 0
                    self.stdout.write('***WKT parse error\n')

                G.node[node.guid]['geometry'] = { "type" : "Point", "coordinates": [ lon , lat ] }    # this is GeoJSON format

            # raw spatial join to find out which nodes are in the freeze footprint
            from django.db import connection, transaction
            queryText =\
            'SELECT\
                  n.guid,max(f.intensity)\
                  FROM\
                  asset_engine.node AS n,\
                  footprints.freeze100 as f\
                  WHERE\
                  ST_Contains(f.geom, n.the_geom)\
                  AND n.layerid < 5\
            GROUP BY\
                  n.guid\
                  ORDER BY n.guid'

            cursor = connection.cursor()
            cursor.execute(queryText)
            footprintNodes = cursor.fetchall()

            # set intensities for those nodes in the footprint
            for footprintNode in footprintNodes:
                G.node[footprintNode[0]]['intensity'] = unicode(footprintNode[1])

            #edgemodel = get_model('laptopsupplychaindemo', 'laptopedge')
            edgemodel = get_model('assetengine', 'GetedgesNoGeom')
            edges = edgemodel.objects.filter(layerid__lte=4)
            for edge in edges:
            #    self.stdout.write(str(node.id))
                if edge.startnodeguid != '0001-106': #this removes the distribution side edges (temporary hack)
                    G.add_edge(edge.startnodeguid,edge.endnodeguid,weight=0,edgeid=edge.guid)

            # writing out timeline record currently disabled
            #edgetimeline = get_model('laptopsupplychaindemo', 'Edgetimeline')

            # this is how to dynamically alter the schema/table that is being accessed
            ####edgetimeline._meta.db_table = '"footprints"."edgetimeline"'
            #edgetimeline.objects.all().delete()

            for n in range(0,int(number_of_turns)):
                self.stdout.write('Starting turn ' + str(n) + '\n')

                for node in nodes:
                    nodetype = node.typecode
                    #self.stdout.write('node ' + str(node.id) + ' type ' + nodetype + '\n')
                    try:
                        #self.stdout.write('incoming edges for node ' + str(node.id) + str(G.in_edges(node.id)) + '\n')
                        incoming_edges = G.in_edges(node.guid)

                        alive = False

                        if nodetype == 'R':
                            alive = True  # raw material nodes always default alive
                            #if  node.id == 29 and n > 4 :  # try killing a node
                            #    alive = False
                        else:
                            # if not a raw material node check all incoming edges have a value of 1
                            alive = True
                            for incoming_edge in incoming_edges:
                                wgt = int(G.edge[incoming_edge[0]][node.guid]['weight'])
                                if wgt == 0:
                                    self.stdout.write('weight on edge '  + str(incoming_edge[0]) + '->' + str(node.guid) + '=' + str(wgt) + '\n')
                                if wgt < 1.0 : alive = False

                            if (node.guid == '0001-106'):
                                if alive:
                                    self.stdout.write('***final assembly node producing\n')
                                else:
                                    self.stdout.write('***final assembly node is not producing\n')

                            if alive:
                                # if still alive decrement incoming edge weights by 1
                                for incoming_edge in incoming_edges:
                                    oldwgt = int(G.edge[incoming_edge[0]][node.guid]['weight'])
                                    newwgt = oldwgt - 1
                                    G.edge[incoming_edge[0]][node.guid]['weight'] = newwgt


                        outgoing_edges = G.out_edges(node.guid)
                        for outgoing_edge in outgoing_edges:
                            oldwgt = int(G.edge[node.guid][outgoing_edge[1]]['weight'])
                            newwgt = oldwgt
                            if alive:
                                newwgt = oldwgt + 1

                            G.edge[node.guid][outgoing_edge[1]]['weight'] = newwgt
                            G.edge[node.guid][outgoing_edge[1]]['value'] = newwgt  #for d3

                            # writing out timeline record currently disabled

                            #new_edge_timeline_record = edgetimeline()
                            #new_edge_timeline_record.edgeid = int(G.edge[node.guid][outgoing_edge[1]]['edgeid'])
                            #new_edge_timeline_record.ownerid = 1
                            #new_edge_timeline_record.lastupdatebyid = 1
                            #new_edge_timeline_record.runid = 1

                            # nb settings.py must have USE_TZ = False
                            #new_edge_timeline_record.lastupdate = datetime.now()

                            #new_edge_timeline_record.timelineposition = n
                            #new_edge_timeline_record.weight = newwgt
                            #try:
                                #new_edge_timeline_record.save()
                            #except BaseException, e:
                            #    self.stdout.write('failed to write to database ' + str(e))


                    except:
                        #self.stdout.write('error in node ' + str(node.id) + '\n')
                        a = 1

            #pos=nx.spring_layout(G)
            #nx.draw(G,pos)
            #plt.savefig('laptop_supply_chain.png')
            #plt.show()
            a = nx.degree_centrality(G)

            #distance_in_metres= 4000000.00

            #nodedist = nodemodel.objects.extra(
            #    select={'the_geom_wkt':'ST_AsText(the_geom)'},
            #    where=["ST_DWithin(geography(the_geom),ST_GeographyFromText('SRID=4326;POINT(0 0)'),%s)"],
            #    params=[distance_in_metres],)

            #print nodedist





            #self.stdout.write('incoming edges for node 106: ' + str(G.in_edges(106)))

            #values = parse_values(PATH_FILE + file_name)

            #from networkx.readwrite import json_graph
            data = json_graph.node_link_data(G)
            import io,json
            json_str = json.dumps(data)
            #with io.open('graph.json', 'w', encoding='utf-8') as outfile:
            #    json.dumps(data,outfile)
            #    outfile.close()
            f = open ('c:\inetpub\wwwroot\d3\graph.json2.txt', 'w')
            f.write( json_str + "\n")
            f.close()




