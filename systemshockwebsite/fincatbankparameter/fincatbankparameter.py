_author__ = 'Simon Ruffle'

from weblib.baseclasses.pagebase import Pagebase

appname = 'fincat'  # must have INSTALLED_APPS = 'modellingengine.fincat' defined in settings.py for this to work
modelname = 'FinCatBankParameter'
formphotosize = 'admin_thumbnail'

editfields = {'include': ('name', 'guid', 'activity', 'organisation', 'place', 'country',  ), 'exclude': None}
displayfields = {'include': ('name', 'guid', 'activity', 'organisation', 'place', 'country',  ), 'exclude': None}

editfields = {'include': None, 'exclude': None}
displayfields = {'include': None, 'exclude': None}

template_name = "fincatbankparameter/templates/fincatbankparameter.html"


class BasicPage (Pagebase):

    def dispatch(self, request, *args, **kwargs):
        self.preProcessPage(request, **kwargs)
        return self.processSimpleForm(request, appname, modelname, formphotosize, template_name, displayfields, editfields, {'foreignkeylinkprefix': ''})