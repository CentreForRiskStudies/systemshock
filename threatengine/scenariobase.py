__author__ = 'Simon Ruffle'

from assetengine.network import *
from footprints.footprint import Footprint


class ScenarioBase():
    def __init__(self):
        self.footprint = None               # the footprint if there is one
        self.additional_attributes = []     # additional node attributes added by the scenario that must be passed to the web client in the JSON string
        self.typeident = 'SBAS'             # identifier
        self.version = '0.0'                # version of model

    def pre_model(self, n, layerid=0, iteration=0):
        pass

    def post_model(self, n, layerid=0, iteration=0):
        pass


class Viewer(ScenarioBase):
    # Simple scenario that does not do anything and can be used to view a network
    def __init__(self):
        ScenarioBase.__init__(self)
        self.typeident = 'SVIW'
        self.version = '0.1'

    def pre_model(self, n, layerid=0, iteration=0):
        ScenarioBase.pre_model(self, n, layerid, iteration)
        pass


class Freeze(ScenarioBase):
    def __init__(self):
        ScenarioBase.__init__(self)
        self.typeident = 'SFRE'
        self.version = '0.1'
        self.additional_attributes = ['intensity']
        self.footprint = Footprint('freeze100', self.additional_attributes)

    def pre_model(self, n, layerid=0, iteration=0):
        ScenarioBase.pre_model(self, n, layerid, iteration)

        # apply footprint
        schema = n.layers[layerid].layerid.schema
        if schema is None:
            schema = 'asset_engine'
        nodetablename = n.layers[layerid].layerid.nodetablename
        if nodetablename is not None:
            nodetablename = schema + '.' + nodetablename
            self.footprint.apply(nodetablename, n.layergraphs[layerid])
        return 0


class BankDefault(ScenarioBase):
    def __init__(self, countrylist):
        ScenarioBase.__init__(self)
        self.countrylist = countrylist
        self.typeident = 'SDEF'
        self.version = '0.1'

    def pre_model(self, n, layerid=0, iteration=0):
        ScenarioBase.pre_model(self, n, layerid, iteration)
        pass






