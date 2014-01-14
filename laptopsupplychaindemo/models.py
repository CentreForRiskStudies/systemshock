# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#     * Rearrange models' order
#     * Make sure each model has one field with primary_key=True
# Feel free to rename the models, but don't rename db_table values or field names.
#
# Also note: You'll have to insert the output of 'django-admin.py sqlcustom [appname]'
# into your database.

from django.db import models


class Event(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    regionid = models.IntegerField()
    typeid = models.IntegerField()
    perilclassid = models.IntegerField()
    periltypeid = models.IntegerField()
    unitsformagnitude = models.CharField(max_length=50, blank=True)
    unitsforintensity = models.CharField(max_length=50, blank=True)
    magnitude = models.FloatField(null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = u'event'

class Laptopnode(models.Model):
    id = models.IntegerField(primary_key=True)
    location = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    place = models.CharField(max_length=255, blank=True)
    organisation = models.CharField(max_length=255, blank=True)
    tier = models.IntegerField(blank=True)
    type = models.CharField(max_length=10, blank=True)
    activity = models.CharField(max_length=255, blank=True)
    url = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'laptopnode'

class Nodetimeline(models.Model):
    id = models.AutoField(primary_key=True)
    nodeid = models.IntegerField(null=True, blank=True)
    timelineposition = models.IntegerField(null=True, blank=True)
    runid = models.IntegerField(null=True, blank=True)
    layerid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    class Meta:
        db_table = u'nodetimeline'

class Laptopedge(models.Model):
    id = models.IntegerField(primary_key=True)
    startnode = models.IntegerField(null=True, blank=True)
    endnode = models.IntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    startlocation = models.CharField(max_length=255, blank=True)
    endlocation = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'laptopedge'

class Intensitytimeline(models.Model):
    id = models.IntegerField(primary_key=True)
    timelineposition = models.IntegerField()
    eventid = models.IntegerField()
    intensitylevel = models.FloatField()
    intensitylevelnormalised = models.FloatField()
    polygonwkt = models.CharField(max_length=1000, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'intensitytimeline'

class Edgetimeline(models.Model):
    id = models.AutoField(primary_key=True)
    edgeid = models.IntegerField(null=True, blank=True)
    timelineposition = models.IntegerField(null=True, blank=True)
    runid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    weight = models.FloatField()
    class Meta:
        db_table = u'asset_engine\".\"edgetimeline'    # how to set schema explicitly

class Bmwedge(models.Model):
    id = models.IntegerField(primary_key=True)
    startnode = models.IntegerField(null=True, blank=True)
    endnode = models.IntegerField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    startlocation = models.CharField(max_length=255, blank=True)
    endlocation = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    class Meta:
        db_table = u'bmwedge'

class Bmwnode(models.Model):
    id = models.IntegerField(primary_key=True)
    location = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    place = models.CharField(max_length=255, blank=True)
    organisation = models.CharField(max_length=255, blank=True)
    type = models.CharField(max_length=10, blank=True)
    activity = models.CharField(max_length=255, blank=True)
    notes = models.CharField(max_length=400, blank=True)
    unknownmetric = models.CharField(max_length=255, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    tier = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'bmwnode'



