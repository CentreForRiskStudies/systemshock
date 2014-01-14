from django.db import models

class Run(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    rundate = models.DateTimeField(null=True, blank=True, verbose_name='Last run date')
    networkid = models.ForeignKey('assetengine.Network', db_column='networkid',verbose_name='Network under test')
    timelinelength = models.IntegerField(null=True, blank=True,verbose_name='Timeline length (units)')
    timelineunits = models.CharField(max_length=50, blank=True,verbose_name='Timeline units')
    status = models.CharField(max_length=255, blank=True, verbose_name='Status of last run')
    results = models.TextField(blank=True)
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'modelling_engine\".\"run'

    def __unicode__(self):
        return self.name


class Runevent(models.Model):
    id = models.IntegerField(primary_key=True)
    runid = models.ForeignKey(Run, db_column='runid')
    eventid = models.ForeignKey('threatengine.Event', db_column='eventid')
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'modelling_engine\".\"runevent'


class Version(models.Model):
    id = models.IntegerField(primary_key=True)
    majorversion = models.IntegerField()
    minorversion = models.IntegerField()
    releasedate = models.DateField()
    notes = models.CharField(max_length=600, blank=True)
    class Meta:
        db_table = u'modelling_engine\".\"version'




