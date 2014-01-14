
from django.db import models


# class GeobaseGeneric(models.Model):
#     id = models.AutoField(primary_key=True)
#     class Meta:
#         db_table = u'asset_engine\".\"geobase_generic'



# class Collaborator(models.Model):
#     id = models.AutoField(primary_key=True)
#     name = models.CharField(max_length=255)
#     lastupdate = models.DateTimeField(null=True, blank=True)
#     lastupdatebyid = models.IntegerField(null=True, blank=True)
#     ownerid = models.IntegerField(null=True, blank=True)
#     class Meta:
#         db_table = u'asset_engine\".\"collaborator'


# Network/Layer depreciated here - only needed to support old supply chain demo

class Network(models.Model):
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

class Layer(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    schema = models.CharField(max_length=50, blank=True)
    nodetablename = models.CharField(max_length=50, blank=True)
    edgetablename = models.CharField(max_length=50, blank=True)
    graphfilename = models.CharField(max_length=255, blank=True)
    typecode = models.CharField(max_length=50, blank=True)
    assetclasscode = models.CharField(max_length=10)
    isdirected = models.CharField(max_length=1)
    geobasetablename = models.CharField(max_length=100, blank=True)
    geobaseidcolumnname = models.CharField(max_length=255, blank=True)
    geobasegeomcolumnname = models.CharField(max_length=255, blank=True)
    geobasenamecolumnname = models.CharField(max_length=100, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    tier = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'asset_engine\".\"layer'

    def __unicode__(self):
        return self.name

class NetworkLayer(models.Model):
    id = models.AutoField(primary_key=True)
    networkid = models.ForeignKey(Network, db_column='networkid')
    layerid = models.ForeignKey(Layer, db_column='layerid')
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"networklayer'


class Country(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='Country name')
    iso3 = models.CharField(max_length=10, unique=True, verbose_name='ISO 3 character country code')

    class Meta:
        db_table = u'base_data\".\"country'
        ordering = ['name']
        managed = False

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return unicode(self.name)

class City(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, verbose_name='City name')
    citycode = models.CharField(max_length=255, unique=True, verbose_name='City code')
    iso3 = models.CharField(max_length=10, unique=True, verbose_name='Country')

    class Meta:
        db_table = u'base_data\".\"city'
        ordering = ['name']
        managed = False

    def __unicode__(self):
        return self.name

# depreciated - only needed to support old supply chain demo
class Node(models.Model):
    id = models.AutoField(primary_key=True)
    regionid = models.IntegerField(null=True, blank=True, default=1)   # TODO this is a FK to region table
    locationwkt = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    place = models.CharField(max_length=255, blank=True)
    organisation = models.CharField(max_length=255, blank=True)
    typecode = models.CharField(max_length=10, blank=True)
    activity = models.CharField(max_length=255, blank=True)
    url = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True,null=True) # This field type is a guess.
    layerid = models.ForeignKey('Layer', db_column='layerid', verbose_name = 'Parent layer')
    name = models.CharField(max_length=100, blank=True)
    boundarycode = models.CharField(max_length=50, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    image1id = models.IntegerField(null=True, blank=True)
    image1photosizeid = models.IntegerField(null=True, blank=True)
    #uuid = models.TextField(blank=True,default='') # This field type is a guess.
    temp = models.FloatField(null=True, blank=True)
    guid = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    class Meta:
        db_table = u'asset_engine\".\"node'

class Edgetimeline(models.Model):
    edgeid = models.IntegerField()
    timelineposition = models.IntegerField(null=True, blank=True)
    runid = models.IntegerField()
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    id = models.AutoField(primary_key=True)
    class Meta:
        db_table = u'asset_engine\".\"edgetimeline'

class Nodetimeline(models.Model):
    nodeid = models.ForeignKey(Node, db_column='nodeid')
    timelineposition = models.IntegerField(null=True, blank=True)
    runid = models.IntegerField()
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    id = models.AutoField(primary_key=True)
    inventory = models.FloatField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"nodetimeline'

class Nodeoutput(models.Model):
    id = models.AutoField(primary_key=True)
    nodeid = models.ForeignKey(Node, db_column='nodeid')
    name = models.CharField(max_length=100, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"nodeoutput'

class Nodeinput(models.Model):
    id = models.AutoField(primary_key=True)
    nodeid = models.ForeignKey(Node, db_column='nodeid')
    name = models.CharField(max_length=100, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"nodeinput'

class Version(models.Model):
    id = models.AutoField(primary_key=True)
    majorversion = models.IntegerField()
    minorversion = models.IntegerField()
    releasedate = models.DateField()
    notes = models.CharField(max_length=600, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"version'

class Lossprofile(models.Model):
    id = models.AutoField(primary_key=True)
    lossclassid = models.ForeignKey('threatengine.Lossclass', db_column='lossclassid')
    atrisklayerid = models.ForeignKey(Layer, db_column='atrisklayerid')
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"lossprofile'



class Edge(models.Model):
    id = models.AutoField(primary_key=True)
    guid = models.CharField(max_length=50)
    startlocationwkt = models.CharField(max_length=255, blank=True)
    endlocationwkt = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    typecode = models.CharField(max_length=10, blank=True)
    name = models.CharField(max_length=100, blank=True)
    costfunctionmultiplier = models.FloatField(null=True, blank=True)
    costfunctionconstant = models.FloatField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    pathwkt = models.CharField(max_length=600, blank=True)
    startnodeuuid = models.TextField(blank=True) # This field type is a guess.
    endnodeuuid = models.TextField(blank=True) # This field type is a guess.
    startnodeguid = models.CharField(max_length=50)
    endnodeguid = models.CharField(max_length=50)
    uuid = models.TextField(blank=True) # This field type is a guess.
    description = models.TextField(blank=True)
    class Meta:
        db_table = u'asset_engine\".\"edge'


class BankSet(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'asset_engine\".\"bankset'

    def __unicode__(self):
        return self.name

# Views
class Getedges(models.Model):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(max_length=50, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    layerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"getedges'

class GetedgesGeomOnFly(models.Model):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(max_length=50, blank=True)
    layerid = models.IntegerField(null=True, blank=True)
    startlocationwkt = models.CharField(max_length=255, blank=True)
    endlocationwkt = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'asset_engine\".\"getedges_geom_on_fly'

class GetedgesNoGeom(models.Model):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(max_length=50, blank=True)
    layerid = models.IntegerField(null=True, blank=True)
    startnodeguid = models.CharField(max_length=50, blank=True)
    endnodeguid = models.CharField(max_length=50, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"getedges_no_geom'

class GetedgesBetweenLayers(models.Model):
    id = models.IntegerField(primary_key=True)
    guid = models.CharField(max_length=50, blank=True)
    startnodeguid = models.CharField(max_length=50, blank=True)
    endnodeguid = models.CharField(max_length=50, blank=True)
    startlayerid = models.IntegerField(null=True, blank=True)
    endlayerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'asset_engine\".\"getedges_between_layers'

