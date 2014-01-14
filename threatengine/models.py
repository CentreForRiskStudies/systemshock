from django.db import models
from weblib.models import WebLibPhoto

class Threatclass(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=255, blank=True)
    shortname = models.CharField(max_length=100, blank=True)
    displayidentifier = models.CharField(max_length=10)
    introtext = models.TextField(blank=True)
    sourcestext = models.TextField(blank=True)
    image1 = models.ForeignKey( WebLibPhoto, db_column='image1id',null=True, blank=True) #if using syncdb change this to PhotologuePhoto and comment out WebLibPhoto
    newssearchterms = models.CharField(max_length=255, blank=True)
    editorname = models.CharField(max_length=100, blank=True)
    weight = models.IntegerField()
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"threatclass'    # how to set schema explicitly
    def __unicode__(self):
        return self.name

class Threattype(models.Model):
    id = models.AutoField(primary_key=True)
    threatclassid = models.ForeignKey(Threatclass, db_column='threatclassid')
    name = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=255, blank=True)
    displayidentifier = models.CharField(max_length=10)
    introtext = models.TextField(blank=True)
    image1 = models.ForeignKey( WebLibPhoto, db_column='image1id',null=True, blank=True) #if using syncdb change this to PhotologuePhoto and comment out WebLibPhoto
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField()
    class Meta:
        db_table = u'threat_engine\".\"threattype'
        managed = False

    def __unicode__(self):
        return self.name

class Threatsubtype(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    weight = models.IntegerField()
    threattypeid = models.ForeignKey(Threattype, db_column='threattypeid')
    class Meta:
        db_table = u'threat_engine\".\"threatsubtype'

class Lookupregion(models.Model):
    id = models.CharField(max_length=10, primary_key=True)
    name = models.CharField(max_length=100)
    weight = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"lookupregion'    # how to set schema explicitly

class Event(models.Model):
    name = models.CharField(max_length=255)
    regioncode = models.ForeignKey(Lookupregion, db_column='regioncode')
    typeid = models.IntegerField()
    unitsformagnitude = models.CharField(max_length=50, blank=True)
    unitsforintensity = models.CharField(max_length=50, blank=True)
    magnitude = models.FloatField(null=True, blank=True)
    probability = models.FloatField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    threatclassid = models.ForeignKey(Threatclass, db_column='threatclassid')
    threattypeid = models.ForeignKey(Threattype, db_column='threattypeid')
    id = models.IntegerField(primary_key=True)
    intensitytimelinetablename = models.CharField(max_length=100, blank=True)
    threatsubtypeid = models.ForeignKey(Threatsubtype, db_column='threatsubtypeid')
    class Meta:
        db_table = u'threat_engine\".\"event'    # how to set schema explicitly

class IntensitytimelineGeneric(models.Model):
    timelineposition = models.IntegerField()
    eventid = models.ForeignKey(Event, db_column='eventid')
    intensitylevel = models.FloatField()
    intensitylevelnormalised = models.IntegerField(unique=True)
    polygonwkt = models.CharField(max_length=1000, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    the_geom = models.TextField(blank=True) # This field type is a guess.
    id = models.IntegerField(primary_key=True)
    class Meta:
        db_table = u'threat_engine\".\"intensitytimeline_generic'


class Lossclass(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    vulnerabilitymetricid = models.IntegerField()
    introtext = models.TextField(blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"lossclass'

class Eventthreatprofile(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, blank=True)
    eventid = models.ForeignKey(Event, db_column='eventid')
    lossclassid = models.ForeignKey(Lossclass, db_column='lossclassid')
    threatutility = models.FloatField()
    introtext = models.TextField(blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"eventthreatprofile'



class Version(models.Model):
    id = models.IntegerField(primary_key=True)
    majorversion = models.IntegerField()
    minorversion = models.IntegerField()
    releasedate = models.DateField()
    notes = models.CharField(max_length=600, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"version'

class Vulnerability(models.Model):
    id = models.IntegerField(primary_key=True)
    intensitylevelnormalised = models.ForeignKey(IntensitytimelineGeneric, db_column='intensitylevelnormalised')
    the_value = models.FloatField()
    lossclassid = models.ForeignKey(Lossclass, db_column='lossclassid')
    lastupdate = models.DateTimeField(null=True, blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)
    class Meta:
        db_table = u'threat_engine\".\"vulnerability'

