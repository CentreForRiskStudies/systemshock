__author__ = 'Simon Ruffle'

from django.db import models


class FinCatRun(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, blank=True)
    networkid = models.ForeignKey('assetengine.Network', db_column='networkid', verbose_name='Network')
    banksetid = models.ForeignKey('assetengine.BankSet', db_column='banksetid', verbose_name='Bank set')
    parameterfile = models.FileField(upload_to='fincat_parameterfiles', max_length=255, blank=True, verbose_name="Upload new parameter defaults", help_text='Note: overwrites all existing model and bank parameter defaults')
    originalparameterfilename = models.CharField(max_length=255, blank=True, verbose_name='Parameter defaults file')
    actualparameterfilename = models.CharField(max_length=255, blank=True, verbose_name='Actual named of saved parameter file (for debugging)')
    lastparameterfileuploaddate = models.DateTimeField(null=True, blank=True, verbose_name='Last parameter defaults file upload date')
    loglevel = models.CharField(max_length=50, default='info')
    randomseed = models.CharField(max_length=50, default='123443', verbose_name='Random seed')

    # Storage of last run info - results holds pickled results dataset
    status = models.CharField(max_length=255, blank=True, verbose_name='Status of last run')
    results = models.TextField(blank=True)
    rundate = models.DateTimeField(null=True, blank=True, verbose_name='Last model run date')

    timelinelength = models.IntegerField(null=True, blank=True,verbose_name='Timeline length (units)')
    timelineunits = models.CharField(max_length=50, blank=True,verbose_name='Timeline units')

    # Model level defaults
    assetsalesfactor = models.FloatField(null=False, default=1.1, verbose_name='Asset sales factor', help_text='factor applied when selling assets')
    maxdefaultratio = models.FloatField(null=False, default=0.9999, verbose_name='Maximum default ratio', help_text='cant default by less than 1 p in 100 pound')
    balancesheetmethod = models.CharField(max_length=50, blank=True, default='capitalratio', verbose_name='Balance sheet method')

    # Economy defaults
    targetcashproportion = models.FloatField(null=False, default=0.0, verbose_name='Target cash proportion')
    firesalefactor = models.FloatField(null=False, default=0.0, verbose_name='Fire sale factor', help_text='factor applied when selling investments')
    investmentcount = models.IntegerField(null=False, default=10, verbose_name='Investment count', help_text='number of investments to create')
    investmentshockfactor = models.FloatField(null=False, default=0.0, verbose_name='Investment shock factor')
    investmentshockproportion = models.FloatField(null=False, default=1.0, verbose_name='Investment shock proportion', help_text='applies to all investments in the economy')

    # Bank defaults
    externalassetratio = models.FloatField(null=False, default=30, verbose_name='External asset ratio')
    capitalratio = models.FloatField(null=False, default=0.06, verbose_name='Capital ratio')
    financialliabilityratio = models.FloatField(null=False, default=0.5, verbose_name='Financial liability ratio')
    cashratio = models.FloatField(null=False, default=0.08, verbose_name='Cash ratio')
    loansize = models.FloatField(null=False, default=10, verbose_name='Loan size')
    loansd = models.FloatField(null=False, default=2, verbose_name='Loan SD')
    homeinvestmentprop = models.FloatField(null=False, default=0.8, verbose_name='Home investment prop', help_text='prop of investments in home economy')
    homeinvestmentdiversity = models.FloatField(null=False, default=0.5, verbose_name='Home investment diversity')
    awayinvestmentdiversity = models.FloatField(null=False, default=0.1, verbose_name='Away investment diversity')
    depositshockfactor = models.FloatField(null=False, default=0.0, verbose_name='Deposit shock factor')
    loanshockfactor = models.FloatField(null=False, default=0.0, verbose_name='Loan shock factor')

    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'modelling_engine\".\"fincat_run'

    def __unicode__(self):
        return self.name


class FinCatBankParameter(models.Model):
    id = models.AutoField(primary_key=True)
    bankguid = models.CharField(max_length=50, blank=True, default='United Kingdom', verbose_name='Bank identifier')   # TODO must make this a FK to Bank
    runid = models.ForeignKey('FinCatRun', db_column='runid', verbose_name='Model run')
    timestepfrom = models.IntegerField(null=True, blank=True)
    timestepto = models.IntegerField(null=True, blank=True)
    externalassetratio = models.FloatField(null=False, default=30, verbose_name='External asset ratio')
    capitalratio = models.FloatField(null=False, default=0.06, verbose_name='Capital ratio')
    financialliabilityratio = models.FloatField(null=False, default=0.5, verbose_name='Financial liability ratio')
    cashratio = models.FloatField(null=False, default=0.08, verbose_name='Cash ratio')
    loansize = models.FloatField(null=False, default=10, verbose_name='Loan size')
    loansd = models.FloatField(null=False, default=2, verbose_name='Loan SD')
    homeinvestmentprop = models.FloatField(null=False, default=0.8, verbose_name='Home investment prop', help_text='prop of investments in home economy')
    homeinvestmentdiversity = models.FloatField(null=False, default=0.5, verbose_name='Home investment diversity')
    awayinvestmentdiversity = models.FloatField(null=False, default=0.1, verbose_name='Away investment diversity')
    depositshockfactor = models.FloatField(null=False, default=0.0, verbose_name='Deposit shock factor')
    loanshockfactor = models.FloatField(null=False, default=0.0, verbose_name='Loan shock factor')
    lastupdatebyid = models.IntegerField(null=True, blank=True)
    lastupdate = models.DateTimeField(null=True, blank=True)
    ownerid = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = u'modelling_engine\".\"fincat_bankparameter'

    def __unicode__(self):
        return 'bank parameter ' + str(self.id)
