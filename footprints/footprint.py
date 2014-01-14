__author__ = 'Simon Ruffle'

from django.db import models
import networkx as nx

# usage
# from footprints.footprint import Footprint
# f = Footprint('freeze100', ['intensity'])  # supply name of shapefile in the footprints schema along with columns to be inherited by spatial query into the nodes affected
# f.footprint.objects.all()  # gets at underlying table
# n.G = f.apply(n.G) # apply footprint to graph


class Footprint:

    footprint = None    # the underlying footprint table can be accessed through this
    attribute_list = [] # list of fields that will be inherited by .apply from the shapefile into the node attributes

    # Dynamic class Factory for footprint table classes.
    # Allows model to be mapped to table and columns at runtime.
    # This gets called by the constructor of this class
    def initFootprintTable(self, footprint_tablename):
        class FootprintTable(models.Model):

            # standard fields of a shape file, only needed if you want to access field through the footprint property of Footprint
            # standardised columns can be mapped to table columns dynamically
            primarykey_colname = 'fid'   # varies between local and server

            primarykey = models.IntegerField(primary_key=True, db_column=primarykey_colname)
            polygonid = models.IntegerField(null=True, blank=True, db_column='id')
            intensity = models.FloatField(null=True, blank=True, db_column='intensity')

            if True:  # you can introduce conditional logic
                intensity2 = models.FloatField(null=True, blank=True, db_column='intensity')


            class Meta:
                db_table = u'footprints\".\"' + footprint_tablename
                managed = False

        return FootprintTable

    def __init__(self, footprint_tablename, the_attribute_list = []):
        self.footprint = self.initFootprintTable(footprint_tablename) # use the class factory to create a class for the footprint table
        self.attribute_list = the_attribute_list

    def set_attribute_list(self, the_attribute_list):
        self.attribute_list = the_attribute_list

    def apply(self, nodetablename, g, timestep=None, delete=False):
        # sets attributes at all nodes in the graph g for the footprint for this scenario
        # the attributes will be as set in inherit_attribute_list
        # timestep is optional and allows the footprint to be defined in a sequence of time steps
        # if delete is true, delete the nodes inside the footprint

        from django.db import connection

        columnlist = ''
        for column in self.attribute_list:
            columnlist += (', max(f.' + column + ')')

        table_name = self.footprint._meta.db_table.replace('"', '')
        if timestep is not None:
            table_name += '_' + str(timestep)

        # raw spatial join to query out nodes that lie in the footprint and get the max value of all the attributes
        # by selecting the max value we get the largest value in the case of overlapping polygons
        queryText =\
            'SELECT n.guid ' + columnlist + ' FROM ' + nodetablename + ' AS n,' \
            + table_name + ' AS f WHERE ST_Contains(f.geom, n.the_geom) GROUP BY n.guid ORDER BY n.guid'

        cursor = connection.cursor()
        cursor.execute(queryText)
        footprintNodes = cursor.fetchall()

        # each footprintNode is a list of column values returned by the query starting with the node GUID

        # set intensities for the nodes inside the footprint
        for footprintNode in footprintNodes:
            key = footprintNode[0]
            if key in g.node.keys():  # check the key exists in case the spatial query returned a node that's not in the graph G
                if delete:
                    g.remove_node(key)
                else:
                    for index, column in enumerate(self.attribute_list, start=1):
                        g.node[key][column] = unicode(footprintNode[index])

        #return g