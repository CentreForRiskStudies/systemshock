__author__ = 'Simon Ruffle'

from modellingbase import ModellingBase
import supplyChainModel as scm

class SupplyChain(ModellingBase):
    def __init__(self, scenario=None):
        ModellingBase.__init__(self, scenario)
        self.typeident = 'MSCH'     # an identifier for the type of model
        self.version = '0.1'        # version of model

    def get_run(self, runid):

        return True

    def run_model(self, network, activelayerid=0, iteration=0):

        self.n = network

        # set up scenario, applying to active layer in network
        if self.s is not None:
            self.s.pre_model(self.n, activelayerid, iteration)

        # modelling code here
        self.n.layergraphs[activelayerid], health = scm.runSimulation(self.n.layergraphs[activelayerid], 10, 999)

        # run any clean up operation by the scenario after the modelling is complete
        if self.s is not None:
            self.s.post_model(self.n, activelayerid, iteration)

        return True

    def get_results(self, cleanjson=True, activelayerid=0, iteration=0):

        # pass the tier attribute as the node style and set up the popup
        for node in self.n.layergraphs[activelayerid].nodes(data=True):
            guid = node[0]
            attributes = node[1]
            #try:
            attributes['nodestyle'] = attributes['tier']
            attributes['popup'] = '<div class="n">Node ' + attributes['guid'] + '</div><div class="t">Tier ' + str(attributes['tier']) + '</div><div class="a">' + attributes['activity'] + '</div><div class="p">' + attributes['name'] + '</div><div class="c">' + unicode(attributes['countrycode']) + '</div><div class="h">Health:' + str(attributes['health']) + '</div>'

            # append the in/out edge count
            attributes['popup'] += '<div class="e">Edges in: ' + unicode(self.n.layergraphs[activelayerid].in_degree(guid)) + ' out: ' + unicode(self.n.layergraphs[activelayerid].out_degree(guid)) + '</div>'
            #except:
            #    pass



        # clear out the attributes we dont need in the JSON string
        if cleanjson:
            additional_attributes = []
            if self.s is not None:
                additional_attributes = self.s.additional_attributes
            self.n.minimise(additional_attributes)

        self.json = self.n.get_json()
        return True

