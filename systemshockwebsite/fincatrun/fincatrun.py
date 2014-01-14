__author__ = 'Simon Ruffle'

from django.shortcuts import render
from weblib.baseclasses.pagebase import Pagebase
from django.forms import ModelForm
from django.http import HttpResponseRedirect,HttpResponse
from datetime import datetime
import platform
from django.core.exceptions import ObjectDoesNotExist
from collections import namedtuple
from assetengine.network import Network
import networkx as nx
from threatengine.scenariobase import BankDefault
from modellingengine.liquidity import Liquidity


# specific to running Fincat
import sys
import cProfile
import cPickle
import base64
import pprint
from modellingengine.fincat.models import FinCatRun
from modellingengine.fincat import simulator, utils

template_dir = 'fincatrun/templates/'

if platform.system() == 'Windows':
    PATH = 'c:\\inetpub\\wwwroot\\pydev\\systemshock\\modellingengine\\fincat\\parameters\\'
else:
    PATH = '/var/lib/geonode/src/GeoNodePy/geonode/modellingengine/fincat/parameters/'


class PageFormEdit (ModelForm):
    class Meta:
        model = FinCatRun
        fields = ('name', 'networkid', 'banksetid', 'parameterfile', )


class PageFormDisplay (ModelForm):
    class Meta:
        model = FinCatRun
        fields = ('networkid', 'banksetid', 'rundate', 'status', 'originalparameterfilename', 'lastparameterfileuploaddate',   )


class FinCatRunPage (Pagebase):

    template_name = template_dir + "fincatrun.html"

    def dispatch(self, request, *args, **kwargs):

        if self.preProcessPage(request, **kwargs):

            # create a structure that will be sent to the web page graph/map viewer
            geonetworkviewerstructure = {}
            geonetworkviewerstructure['startup'] = {}

            tabmode = 'list'
            viewertabmode = 'list'
            self.page_context['init_code'] = ''
            try:
                if request.REQUEST['tab'] == 'map':
                    tabmode = 'map'
                    viewertabmode = 'map'
                if request.REQUEST['tab'] == 'list':
                    tabmode = 'list'
                    viewertabmode = 'list'
                if request.REQUEST['tab'] == 'topo':
                    tabmode = 'map'
                    viewertabmode = 'topo'
                    self.page_context['init_code'] = 'toggle();'
            except:
                pass
            self.page_context['tabmode'] = tabmode
            geonetworkviewerstructure['startup']['tabmode'] = str(viewertabmode).lower

            displayiteration = 'final'
            iteration = 1
            try:
                if request.REQUEST['iter'] == 'start':
                    displayiteration = 'start'
                    iteration = 0
            except:
                pass
            self.page_context['iter'] = displayiteration

            api = request.GET.get('api')
            if api is None or api == '' or api == 'leaflet':
                api = 'leaflet'
            else:
                api = 'OL'
            self.page_context['api'] = api

            stage = 0
            try:
                if request.REQUEST['stage']:
                    stage = int(request.REQUEST['stage'])
            except:
                pass
            self.page_context['stage'] = stage

            # process what gets displayed in the text box and the functions of the next and previous buttons
            page_subtitle = 'unknown'
            nextbutton = ''
            prevbutton = ''
            starttext = ''

            if stage == 0:
                prevbutton = ''
                nextbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=1&tab=topo&iter=start">next &raquo;</a>'
                starttext = 'Basic diagnostic information for the last run of the model. To page through the model&#39;s outputs in map and topological forms click on <b>next</b>'
                page_subtitle = 'Model Status Display'

            if stage == 1:
                prevbutton = ''
                nextbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=2&tab=map&iter=start">next &raquo;</a>'
                starttext = 'The world&#39;s financial system can be represented by a &#39;Core Periphery&#39; network model. This interactive model shows a simplified representation with each country represented by a single node, based on data from the IMF. Your cursor will show data about each country&#39;s banking system, regulatory regions and capital ratio at the start of the model run. This draggable, force-directed graph shows the dark green core banks, serving many light green periphery banking systems. '
                page_subtitle = '1. The Global Banking Network'

            if stage == 2:
                prevbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=1&tab=topo&iter=start">&laquo; previous</a>'
                nextbutton = '<a href="/page/28">next &raquo;</a>'
                starttext = 'The banking network can be seen geographically. This screen shows the initial conditions of the model with the global banking network shown on a world map. Each central bank is shown in its capital city. "Core" banks are shown darker green. Mouse over each bank to get more details.  '
                page_subtitle = '2. The Geography of Banking'

            if stage == 6:
                prevbutton = '<a href="/page/27">&laquo; previous</a>'
                nextbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=7&tab=topo&iter=final">next &raquo;</a>'
                starttext = 'This screen shows a subset of the iterations of the model. Key central banks are shown with their balance sheets taken at iteration points in the model as they change.'
                page_subtitle = '6. Model Run Progression'

            if stage == 7:
                prevbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=6&tab=list">&laquo; previous</a>'
                nextbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=8&tab=map&iter=final">next &raquo;</a>'
                starttext = 'The banking network at the end of the model run shows the capital ratios of the banks that are worst affected, from green to red, with red being worst. The model provides a lot of detailed data of the crisis progression for analysis.'
                page_subtitle = '7. Contagion Mapping'

            if stage == 8:
                prevbutton = '<a href="/fincatrun/' + self.page_context['ix'] + '?stage=7&tab=topo&iter=final">&laquo; previous</a>'
                nextbutton = '<a href="/page/21">next &raquo;</a>'
                starttext = 'The crisis in the international banking network can be seen geographically. The contagion has spread from its initial starting point and has impacted many countries throughout Europe and has affected countries further afield.'
                page_subtitle = '8. The Geography of the Financial Crisis'

            self.page_context['nextbutton'] = nextbutton
            self.page_context['prevbutton'] = prevbutton
            self.page_context['starttext'] = starttext

            self.page_context['results'] = {'entity': [], 'targeturl': '', 'fields': [] }

            current_object = None

            if not self.page_context['addmode']:  # we are reading an existing record
                try:
                    current_object = FinCatRun.objects.get(pk=self.page_context['ix'])
                except ObjectDoesNotExist:
                    return self.showErrorPage(request, 'Error: Record ' + str(self.page_context['ix']) + ' does not exist')
                except:
                    return self.showErrorPage(request, 'Error: invalid parameter supplied')

                self.page_context['current_object'] = current_object
                self.page_context['page_title'] = current_object.name
                #page_subtitle = current_object.name
                self.page_context['page_subtitle'] = page_subtitle

                # get the picked results data structure from the last run of this model instance
                if not self.page_context['editmode'] and current_object.results is not None and current_object.results != '':
                    results = cPickle.loads(base64.b64decode(current_object.results))

                    balanceSheets = results[0][0]   # when bankId lending investments cash borrowing deposits capital
                    borrowings = results[0][1]      # when fromBankId toBankId amount
                    defaults = results[0][2]        # when bankId ratio
                    holdings = results[1][0]        # when investmentId bankId amount
                    prices = results[1][0]          # when investmentId price

                    # results table

                    fieldlist = \
                        [
                            [{'bankId':  {'title': 'Bank id', 'type': 'CharField', }}],
                            [{'when':  {'title': 'Iteration', 'type': 'IntegerField', }}],
                            [{'lending':  {'title': 'Lending', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'investments':  {'title': 'Investments', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'cash':  {'title': 'Cash', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'borrowing':  {'title': 'Borrowing', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'deposits':  {'title': 'Deposits', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'capital':  {'title': 'Capital', 'type': 'DecimalField', 'decimal_places': 1, }}],
                            [{'capitalratio':  {'title': 'Capital ratio %', 'type': 'DecimalField', 'decimal_places': 1, }}],
                        ]

                    balanceSheets2 = [balanceSheet for balanceSheet in balanceSheets if balanceSheet.bankId in ['Japan', 'United Kingdom', 'France', 'United States', 'Greece','Italy', 'Germany', 'China','Russia','Spain']]
                    from operator import itemgetter, attrgetter
                    balanceSheets3 = sorted(balanceSheets2, key=attrgetter('bankId'), reverse=False)

                    balanceSheet4 = []
                    for b in balanceSheets3:
                        # create a new named tuple type by adding a field to the balance sheet named tuple
                        newtupletype = namedtuple ('BalanceSheet', b._fields+('capitalratio',))
                        # copy values across
                        d = newtupletype(b.when,b.bankId,b.lending,b.investments,b.cash,b.borrowing,b.deposits,b.capital,(b.capital/(b.lending+b.investments+b.cash))*100)
                        balanceSheet4.append(d)

                    resultsFields = {'entity': balanceSheet4, 'targeturl': '/bank/', 'fields': fieldlist }
                    self.page_context['results'] = resultsFields

                    n = Network()
                    #try:
                    #    ix = int(self.page_context['ix'])
                    #except:
                    #    return self.showErrorPage(request, 'Invalid network id')

                    status = n.load(7)  # load a network from the asset engine database by its network id

                    if not status:
                        return self.showErrorPage(request, 'Error loading network : ' + n.statusMessage)

                    # make default popup
                    n.makePopup()

                    # get network metrics
                    geonetworkviewerstructure['metrics'] = n.getMetrics()

                    # iterate the banks in the network
                    for node in n.layergraphs[0].nodes(data=True):

                        nodeid = node[0] #node array index 0 is the node id, index 1 is the attribute list
                        attributes = node[1]
                        attributes['intensity'] = 0
                        attributes['guid'] = nodeid

                        count = n.layergraphs[0].in_degree(nodeid)

                        # if the tier is not already defined in the file, define it
                        if 'tier' not in attributes:

                            # base tier on number of incoming edges
                            tier = 3
                            if count > 8:
                                tier = 2
                            if count > 15:
                                tier = 1
                            if attributes['core'] == 'True':
                                tier = 0

                        else:
                            tier = attributes['tier']

                        in_edges = n.layergraphs[0].in_edges(nodeid)  # gets inward edges
                        for edge in in_edges:
                            # create a tier attribute on the edge
                            n.layergraphs[0][edge[0]][edge[1]]['tier']=tier
                            n.layergraphs[0][edge[0]][edge[1]]['linkstyle'] = 0

                        attributes['tier'] = tier
                        attributes['popup'] = '<div class="n">' + attributes['region'] + '</div><div class="a">' + attributes['label'] + '</div><div>Outward links:' + unicode(n.layergraphs[0].out_degree(nodeid)) + '</div><div>Inward links:' + unicode(n.layergraphs[0].in_degree(nodeid)) + '</div>'

                        bankId = attributes['label']
                        # each bank has several balance sheet records taken as the model runs
                        allBSRecords = [balanceSheet for balanceSheet in balanceSheets if balanceSheet.bankId in [bankId]]
                        # initial balance sheet record
                        initBSRecord = allBSRecords[0]
                        # the last balance sheet record is the final result
                        finalBSRecord = allBSRecords[-1]
                        # compute capital ratio
                        initcapratio = (initBSRecord.capital/(initBSRecord.lending+initBSRecord.investments+initBSRecord.cash))*100
                        finalcapratio = (finalBSRecord.capital/(finalBSRecord.lending+finalBSRecord.investments+finalBSRecord.cash))*100
                        # store as an attribute on the bank node
                        attributes['initcapratio'] = round(initcapratio, 1)
                        attributes['finalcapratio'] = round(finalcapratio, 1)

                        tier = 3 # banks in good shape - capratio > 5.5

                        # core banks in good shape
                        if attributes['core'] == 'True':
                                tier = 4

                        if finalcapratio < 0.02:
                            tier = 0
                        else:
                            if finalcapratio < 2.0:
                                tier = 1
                            else:
                                if finalcapratio < 4.0:
                                    tier = 2
                                else:
                                    if finalcapratio < 5.5:
                                        tier = 3

                         # if an iter querystring parameter was set to 'start' then
                         # color up nodes by whether they are core or not
                        if displayiteration == 'start':
                            tier = 3

                            if attributes['core'] == 'True':
                                tier = 4

                        attributes['tier'] = tier
                        attributes['nodestyle'] = tier

                        # add the cap ratio to the popup
                        if displayiteration == 'start':
                            attributes['popup'] = attributes['popup'] + '<br/>Init cap ratio ' + unicode(round(initcapratio, 1)) + '%'
                        else:
                            attributes['popup'] = attributes['popup'] + '<br/>Final cap ratio ' + unicode(round(finalcapratio, 1)) + '%'

                        # add in if its core
                        if attributes['core'] == 'True':
                            attributes['popup'] = attributes['popup'] + '<br/>Core'

                    # to reduce the size of the JSON string, we delete the node attributes we dont need,
                    #n.minimise()

                    #jsonGraphStr = n.get_json()
                    #self.page_context['jsonGraph'] = jsonGraphStr

                    bankdefault = BankDefault(['Greece', 'Cyprus'])  # get scenario
                    liquiditymodel = Liquidity(bankdefault)
                    liquiditymodel.get_run(self.page_context['ix']) # load previous model run from database
                    activelayer = 0
                    liquiditymodel.run_model(n, activelayer, iteration)  # TODO we actually need to run the model in the POST, not here
                    liquiditymodel.get_results(True, activelayer, iteration)
                    geonetworkviewerstructure['jsonGraph'] = liquiditymodel.json


            # other info to pass through the page context
            self.page_context['pageclass'] = 'fincatrun'
            self.page_context['editlink'] = ('/' + 'fincatrun' + '/' + str(self.page_context['ix'])).lower()

            # pass the data to the geonetwork viewer template tag
            geonetworkviewerstructure['uniqueid'] = 1  # allows multiple viewers on same page
            self.page_context['geonetworkviewer1'] = geonetworkviewerstructure


            ###############
            # POST
            ###############

            if request.method == 'POST':

                if self.page_context['addmode']:  # new record, create at first with default values
                    current_object = FinCatRun()
                    current_object.name = 'untitled'
                    #current_object.networkid = Network.objects.get(pk=1)
                    current_object.lastupdate = datetime.now()
                    current_object.lastupdatebyid = request.user.id
                    current_object.ownerid = request.user.id
                    current_object.status = 'not run yet, or run failed'
                    self.page_context['editmode'] = True  # in case it turns out there is an error in input

                # read the page form
                # note as we upload a file here, we need enctype="multipart/form-data" in the <form> tag and to add request.FILES, to the call below
                pageFormEdit = PageFormEdit(request.POST, request.FILES, instance=current_object , prefix='mainpageform') # A form bound to the POST data, prefix allows multiple forms

                if pageFormEdit.is_valid():  # All validation rules pass

                    self.page_context['editmode'] = False # no errors

                    # now create the record in the database
                    current_object.save()

                    # now we know the new record's id
                    self.page_context['ix'] = current_object.id
                    self.page_context['current_object'] = current_object

                    # now save the screen form values into the database
                    pageFormEdit.save()

                    # see if a parameter file got uploaded
                    if current_object.parameterfile.name != '':
                        # process a new parameter file here into the fincat_bankparameters table
                        # first erase all pre-existing records, if any, with runid equal to this one

                        # after a successful upload of the parameter file, we need to delete it from the record so it does not get reuploaded every time
                        # but we save its name in a separate field
                        current_object.originalparameterfilename = unicode(request.FILES['mainpageform-parameterfile'])
                        current_object.actualparameterfilename = current_object.parameterfile.name
                        current_object.lastparameterfileuploaddate = datetime.now()
                        current_object.parameterfile = None

                    # run the model
                    pList, basicGraph = utils.read_params_file(PATH, 'countries1.xml')
                    results = simulator.setup_simulation(pList, basicGraph)

                    current_object.rundate = datetime.now()
                    current_object.status = 'Success'
                    current_object.results = base64.b64encode(cPickle.dumps(results, cPickle.HIGHEST_PROTOCOL))
                    current_object.save()

                    return HttpResponseRedirect('/fincatrun/' + str(self.page_context['ix'])) # Redirect after successful POST to the non editing version
                else:

                    self.page_context['form'] = pageFormEdit

                    return render(request, self.template_name, self.page_context)  # Error - return just the form when there is an error - the template must not try and render anything outside the form because the contact data is not present


            ###############
            # GET
            ###############

            if request.method == 'GET':

                if self.page_context['addmode']:  # new record - initialise a dummy record that we dont save with defaults to see on the page
                    current_object = FinCatRun()
                    current_object.name = 'untitled'
                    #current_object.networkid = Network.objects.get(pk=1)
                    self.page_context['editmode'] = True

                if self.page_context['editmode']:  # edit or add mode
                    current_object.status = 'Pending run...'
                    pageFormEdit = PageFormEdit(instance=current_object, prefix="mainpageform") # prefix allows multiple forms
                    self.page_context['form'] = pageFormEdit
                else:
                    pageFormDisplay = PageFormDisplay (instance=current_object) # display mode
                    pagefields = self.createFormFieldStructure( pageFormDisplay, current_object )
                    self.page_context['tablesetup1'] = pagefields  # pass field structure to generictablerenderer

                return render(request, self.template_name, self.page_context)
