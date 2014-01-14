__author__ = 'Simon Ruffle'

from django.db import transaction
from assetengine.network import Network
from threatengine.scenariobase import ScenarioBase
from footprints.footprint import Footprint
from django.db.models import get_model
from networkx.readwrite import json_graph
import json
from datetime import datetime


class ModellingBase:
    def __init__(self, scenario=None):
        self.run_record = None      # the record the represents the current run
        self.n = None               # the network
        self.s = scenario           # the scenario
        self.json = ''              # JSON string suitable for sending to web client
        self.statusmessage = ''     # Error message if return status false
        self.typeident = 'MBAS'     # an identifier for the type of model
        self.version = '0.0'        # version of model

    def get_run(self, runid):
        # loads the run record from the database by its id
        return True

    def run_model(self, network, activelayerid=0, iteration=0):
        # basic pattern for function that runs a scenario + model combination
        # this function can be used to execute a scenario without a model
        # and can be used for basic viewing of networks

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

        # clear out the attributes we dont need in the JSON string
        if cleanjson:
            additional_attributes = []
            if self.s is not None:
                additional_attributes = self.s.additional_attributes
            self.n.minimise(additional_attributes)

        self.json = self.n.get_json()
        return True