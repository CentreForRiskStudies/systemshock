__author__ = 'Simon Ruffle'

from modellingbase import ModellingBase
from datetime import datetime
from collections import namedtuple
import cPickle
import base64
from modellingengine.fincat.models import FinCatRun
from modellingengine.fincat import simulator, utils
from django.core.exceptions import ObjectDoesNotExist

class Liquidity(ModellingBase):
    def __init__(self, scenario=None):
        ModellingBase.__init__(self, scenario)
        self.typeident = 'MLIQ'     # an identifier for the type of model
        self.version = '0.1'        # version of model

    def create_new_run(self, request, ):
        new_run = FinCatRun()
        new_run.name = 'untitled'
        new_run.lastupdate = datetime.now()
        new_run.lastupdatebyid = request.user.id
        new_run.ownerid = request.user.id
        new_run.status = 'not run yet, or run failed'
        self.run_record = new_run

    def get_run(self, runid):
        try:
            self.run_record = FinCatRun.objects.get(pk=runid)
        except ObjectDoesNotExist:
            self.statusmessage = 'Error: Record ' + str(self.page_context['ix']) + ' does not exist'
            return False
        except:
            self.statusmessage =  'Error: invalid parameter supplied'
            return False

        return True

    def run_model(self, network, activelayerid=0, iteration=0):

        self.n = network

        # set up scenario, applying to active layer in network
        if self.s is not None:
            self.s.pre_model(self.n, activelayerid, iteration)

        # modelling code here

        # run any clean up operation by the scenario after the modelling is complete
        if self.s is not None:
            self.s.post_model(self.n, activelayerid, iteration)

        return True

    def get_results(self, cleanjson=True, activelayerid=0, iteration=0):

        # iterate nodes
        for node in self.n.layergraphs[activelayerid].nodes(data=True):
            guid = node[0]
            attributes = node[1]

        # clear out the attributes we dont need in the JSON string
        if cleanjson:
            additional_attributes = []
            if self.s is not None:
                additional_attributes = self.s.additional_attributes
            self.n.minimise(additional_attributes)

        self.json = self.n.get_json()
        return True


