__author__ = 'Louise'

import random
import xml.etree.ElementTree as ET

from nose.tools import eq_
import networkx as nx

import FinCat.simulator as simulator
import FinCat.network as network
import FinCat.results as results
from FinCat.economy import Economy
from FinCat.bank import Bank
from FinCat.utils import Parameters, read_params_from_xml, SimulationInfo
from utils import approx_equal


class TestUpdate:
    def setUp(self):
        self.simInfo = SimulationInfo()
        parameterDefs = simulator.define_parameters()
        eParams = Parameters(parameterDefs)
        self.simInfo.theParameters = eParams
        self.econ = Economy(self.simInfo, "Economy1", eParams)
        self.banks = []
        self.investments = []
        for i in range(5):
            params = Parameters(parameterDefs, self.econ.params)
            self.banks.append(Bank(self.simInfo, "bank%s" % i, self.econ, params))
            self.investments.append(self.econ.create_investment())

        random.seed(1234)

    def test_loan_default(self):

        for i in range(4):
            # a chain of banks
            loanAmount = 5 * (i + 1)
            self.simInfo.loanNetwork.add_edge(self.banks[i + 1], self.banks[i], amount=loanAmount)
            self.banks[i].cash = 6
        self.banks[0].deposits = 2
        self.banks[4].deposits = 19
        # at the outset, bank has capital -1, 1-4 have capital 1,
        for b, cap in zip(range(5), [-1, 1, 1, 1, 1]):
            bc = self.banks[b].equity_value()
            eq_(cap, bc, "Expected bank %s to have capital %r but has %r" % (b, cap, bc))
        simulator.do_updates(self.simInfo)
        bankHistories = results.collect_bank_histories(self.simInfo)
        # they should all have gone bust
        for b in range(5):
            assert self.banks[b].totalDefault < 1.0, "expected bank %s to have defaulted but it has not" % b
        eq_(5, len(bankHistories.defaults), "5 banks should be bust but there are %r" % len(bankHistories.defaults))
        # and they should be in order
        for b in range(5):
            eq_(bankHistories.defaults[b][1], self.banks[b].id_,
                "expected %r to go bust would be %r but it is %r" % (b, self.banks[b], bankHistories.defaults[b][1]))

    def test_investment_default1(self):

        self.simInfo.theParameters.set('assetSalesFactor', 1.2)   # fudge factor
        self.simInfo.theParameters.set('targetCashProportion', 0.0)

        self.econ.params.set('fireSaleFactor', 5.0)  # large fire sale effect

        for i in range(4):
            # a chain of banks
            self.investments[i].buy(10, self.banks[i])
            self.investments[i].buy(10, self.banks[i + 1])
            self.banks[i + 1].deposits = 15
        self.investments[0].buy(10, self.banks[0])
        self.investments[3].buy(10, self.banks[4])
        self.banks[0].cash = -15
        # at the outset, they all have capital 5
        for b, cap in zip(range(5), [5, 5, 5, 5, 5]):
            bc = self.banks[b].equity_value()
            eq_(cap, bc, "Expected bank %s to have capital %r but has %r" % (b, cap, bc))
            # bank 0 is going to have to sell its investments
        simulator.do_updates(self.simInfo)
        # 2 should have gone bust. bank 0 will have sold a lot of investment 0, which will make bank 1 bust.
        # but bank 1 has no reason to sell, so no other banks feel the effects.
        assert self.banks[0].totalDefault < 1.0, "bank 0 should have defaulted but has not"
        assert self.banks[1].totalDefault < 1.0, "bank 1 should have defaulted but has not"
        balanceSheetHistories, borrowingHistories, defaultHistories = results.collect_bank_histories(self.simInfo)
        investmentHistories = results.collect_investment_histories(self.simInfo)
        eq_(2, len(defaultHistories), "Should be 2 default events but got %r" % len(defaultHistories))
        # and they should be in order
        for b in range(len(defaultHistories)):
            eq_(defaultHistories[b][1], self.banks[b].id_,
                "expected %r to go bust would be %r but it is %r" % (b, self.banks[b], defaultHistories[b][1]))
        pHistories = investmentHistories.prices
        eq_(6, len(pHistories), "expected 6 price records but got %r" % len(pHistories))
        lastPrice = pHistories[-1]
        eq_(2, lastPrice.when, "expected last price record to have time 2 but got %r" % lastPrice.when)
        eq_(self.investments[0].id_, lastPrice.investmentId,
            "expected last price record to be for %r but got %r" % (self.investments[0].id_, lastPrice.investmentId))
        hHistories = investmentHistories.holdings
        lastHolding = hHistories[-1]
        eq_(2, lastHolding.when, "expected last holding change to be at time 2 but got %r" % lastHolding.when)
        eq_(self.investments[0].id_, lastHolding.investmentId,
            "expected last holding record to be for %r but got %r" % (self.investments[0].id_,
                                                                      lastHolding.investmentId))

    def test_investment_default2(self):

        self.econ.params.set('fireSaleFactor', 5.0)  # large fire sale effect
        self.econ.params.set('assetSalesFactor', 1.2)  # fudge factor
        self.econ.params.set('targetCashProportion', 0.0)  # non-negative cash

        for i in range(5):
            # disconnected banks
            self.investments[i].buy(20, self.banks[i])
            self.banks[i].deposits = 15
            # at the outset, they all have capital 5
        for b, cap in zip(range(5), [5, 5, 5, 5, 5]):
            bc = self.banks[b].equity_value()
            eq_(cap, bc, "Expected bank %s to have capital %r but has %r" % (b, cap, bc))

        self.econ.do_deposit_withdrawals(.9)
        simulator.do_updates(self.simInfo)
        for b in range(5):
            assert self.banks[b].totalDefault < 1.0, "expected bank %s to have defaulted but it has not" % b
            # 5 should have gone bust. They will all sell assets, whose price will fall.


class TestSetup():
    def setup(self):
        self.simInfo = SimulationInfo()

        self.simInfo.runDesc = "testTest"
        self.simInfo.tString = "timeString000"

        self.parameterDefs = simulator.define_parameters()
        xmlString = ("<parameters name='test1'>" +
                     "<simulator>" +
                     "<parameter name='assetSalesFactor' value='1.0' />" +
                     "<parameter name='randomSeed' value='12343' />" +
                     "<parameter name='balanceSheetMethod' value='assets' />" +
                     "</simulator>" +
                     "<economy name='econ1'>" +
                     "<parameter name='fireSaleFactor' value='0.0' />" +
                     "<parameter name='investmentCount' value='5' />" +
                     "<parameter name='financialAssetRatio' value='0.3' />" +
                     "<parameter name='capitalRatio' value='.15' />" +
                     "<parameter name='financialLiabilityRatio' value='.7' />" +
                     "</economy>" +
                     "<economy name='econ2'>" +
                     "<parameter name='fireSaleFactor' value='0.5' />" +
                     "<parameter name='investmentCount' value='10' />" +
                     "<parameter name='cashRatio' value='.15' />" +
                     "<parameter name='financialAssetRatio' value='0.4' />" +
                     "<parameter name='capitalRatio' value='0.2' />" +
                     "<parameter name='financialLiabilityRatio' value='.7' />" +
                     "</economy>" +
                     "<bank name='bank1' economy='econ1'>" +
                     "<parameter name='loanSize' value='10' />" +
                     "<parameter name='loanSD' value='2' />" +
                     "<parameter name='cashRatio' value='.1' />" +
                     "</bank>" +
                     "<bank name='bank2' economy='econ2'>" +
                     "<parameter name='loanSize' value='20' />" +
                     "<parameter name='loanSD' value='2' />" +
                     "<parameter name='financialLiabilityRatio' value='.2' />" +
                     "</bank>" +
                     "<bank name='bank3' economy='econ2'>" +
                     "<parameter name='loanSize' value='30' />" +
                     "<parameter name='loanSD' value='3' />" +
                     "<parameter name='financialAssetRatio' value='0.25' />" +
                     "<parameter name='capitalRatio' value='.125' />" +
                     "</bank>" +
                     "</parameters>")
        self.xmlRoot = ET.fromstring(xmlString)
        self.pList = read_params_from_xml(self.xmlRoot, "fName")
        self.simInfo.basicGraph = nx.DiGraph()
        self.simInfo.basicGraph.add_edges_from([('bank1', 'bank2'), ('bank2', 'bank1'),
                                             ('bank2', 'bank3'), ('bank3', 'bank1')])
        simulator.do_simulator_parameters(self.simInfo, self.pList, self.parameterDefs)

    def test_economies(self):
        simulator.do_economy_parameters(self.simInfo, self.pList, self.parameterDefs)
        # we expect there to be two economies
        eq_(len(self.simInfo.economyDirectory), 2, "expected 2 economies but there are %r" % len(self.simInfo.economyDirectory))
        assert "econ1" in self.simInfo.economyDirectory, "expected econ1 to be in the directory"
        assert "econ2" in self.simInfo.economyDirectory, "expected econ2 to be in the directory"
        e1 = self.simInfo.economyDirectory["econ1"]
        e2 = self.simInfo.economyDirectory["econ2"]
        simulator.reset_economies(self.simInfo)
        # we expect 5 and 10 investments
        eq_(len(e1.investments), 5, "expected econ1 to have 5 investments but it has %r" % len(e1.investments))
        eq_(len(e2.investments), 10, "expected econ2 to have 5 investments but it has %r" % len(e2.investments))
        # check that the parenting of parameters is working
        p1 = e1.params.get('randomSeed')
        eq_(p1, '12343')
        e1.create_investments(6)   # create another 6
        eq_(len(e1.investments), 11, "expected econ1 to have 11 investments but it has %r" % len(e1.investments))
        # now reset again
        simulator.reset_economies(self.simInfo)
        eq_(len(e1.investments), 5, "expected econ1 to have 5 investments again but it has %r" % len(e1.investments))

    def test_banks_assets(self):
        simulator.do_economy_parameters(self.simInfo, self.pList, self.parameterDefs)
        simulator.do_bank_parameters(self.simInfo, self.pList, self.parameterDefs)
        eq_(len(self.simInfo.bankDirectory), 3, "Expected 3 banks but got %r" % len(self.simInfo.bankDirectory))
        b1 = self.simInfo.bankDirectory["bank1"]
        b2 = self.simInfo.bankDirectory["bank2"]
        e1 = self.simInfo.economyDirectory["econ1"]
        e2 = self.simInfo.economyDirectory["econ2"]
        eq_(b1.economy, e1, "expected bank1's economy to be econ1 but is %r" % b1.economy)
        eq_(b2.economy, e2, "expected bank2's economy to be econ2 but is %r" % b2.economy)
        assert simulator.check_bank_nodes(self.simInfo)
        simulator.reset_economies(self.simInfo)
        simulator.reset_banks(self.simInfo)
        # expect the following bank loans to be in place:
        # bank1 -> bank2, mean size 10
        # bank2 -> bank1, mean size 20
        # bank2 -> bank3, mean size 20
        # bank3 -> bank1, mean size 30
        b3 = self.simInfo.bankDirectory["bank3"]
        for bFrom, bTo, bl in zip([b1, b2, b2, b3], [b2, b1, b3, b1], [10, 20, 20, 30]):
            lending = network.bank_lending(self.simInfo, bFrom, bTo)
            assert abs(bl - lending) < 10, ("expected lending from %s to %s to be roughly %r but is %r" %
                                            (bFrom.id_, bTo.id_, bl, lending))
            borrowing = network.bank_borrowing(self.simInfo, bTo, bFrom)
            assert abs(bl - borrowing) < 10, ("expected borrowing to %s from %s to be roughly %r but is %r" %
                                              (bTo.id_, bFrom.id_, bl, borrowing))
        for b, far, cr, capR in zip([b1, b2, b3], [0.30, 0.40, 0.25], [0.1, 0.15, 0.15], [0.15, .2, .125]):
            assert approx_equal(b.total_assets(), b.total_liabilities() + b.equity_value(), .0000001), \
                "Expected %s balance sheet to balance: assets %f, liabilities %f, capital %f" % (
                    b.id_, b.total_assets(), b.total_liabilities(), b.equity_value())
            thisFar = b.financial_asset_ratio()
            thisCr = b.cash / b.total_assets()
            thisCapR = b.equity_value() / b.total_assets()
            if b.deposits > 0:   # there was no hanky panky
                assert approx_equal(far, thisFar, .0000001), ("Expected %s financial asset ratio to be %f but is %f" %
                                                            (b.id_, far, thisFar))
                assert approx_equal(cr, thisCr, .0000001), ("Expected %s cash ratio to be %f but is %f" % (b.id_, cr, thisCr))
                assert approx_equal(capR, thisCapR, .0000001), ("Expected %s capital ratio to be %f but is %f" %
                                                                (b.id_, capR, thisCapR))
            else:
                assert thisFar < far, ("Expected %s financial asset ratio to be less than %f but is %f" %  (b.id_, far, thisFar))
                assert thisCr > cr, ("Expected %s cash ratio to be greater than %f but is %f" % (b.id_, cr, thisCr))
                assert thisCapR < capR, ("Expected %s capital ratio to be less than %f but is %f" %
                                         (b.id_, capR, thisCapR))


    def test_banks_liabilities(self):
        simulator.do_economy_parameters(self.simInfo, self.pList, self.parameterDefs)
        simulator.do_bank_parameters(self.simInfo, self.pList, self.parameterDefs)
        self.simInfo.theParameters.set('balanceSheetMethod', 'liabilities')
        b1 = self.simInfo.bankDirectory["bank1"]
        b2 = self.simInfo.bankDirectory["bank2"]
        simulator.reset_economies(self.simInfo)
        simulator.reset_banks(self.simInfo)
        # expect the following bank loans to be in place:
        # bank1 -> bank2, mean size 10
        # bank2 -> bank1, mean size 20
        # bank2 -> bank3, mean size 20
        # bank3 -> bank1, mean size 30
        b3 = self.simInfo.bankDirectory["bank3"]

        for b, capR, flr, cr in zip([b1, b2, b3], [0.15, .2, .125], [0.7, 0.2, 0.7],
                                    [0.1, 0.15, 0.15]):
            assert approx_equal(b.total_assets(), b.total_liabilities() + b.equity_value(), .0000001), \
                "Expected %s balance sheet to balance: assets %f, liabilities %f, capital %f" % (
                    b.id_, b.total_assets(), b.total_liabilities(), b.equity_value())
            thisCapR = b.equity_value() / b.total_assets()
            thisFlr = b.financial_liability_ratio()
            thisCr = b.cash / b.total_assets()
            thisInv = b.investment_value()
            if thisInv > 0:  # no hanky panky
                assert approx_equal(capR, thisCapR, .0000001), ("Expected %s capital ratio to be %f but is %f" %
                                                                                                        (b.id_, capR, thisCapR))
                assert approx_equal(flr, thisFlr, .0000001), ("Expected %s financial liability ratio to be %f but is %f" %
                                                              (b.id_, flr, thisFlr))
                assert approx_equal(cr, thisCr, .0000001), ("Expected %s cash ratio to be %f but is %f" % (b.id_, cr, thisCr))
            else:
                assert thisCapR < capR, ("Expected %s capital ratio to be less than %f but is %f" %
                                         (b.id_, capR, thisCapR))
                assert thisFlr < flr, ("Expected %s financial liability ratio to be less than %f but is %f" %
                                       (b.id_, flr, thisFlr))
                assert thisCr < cr, ("Expected %s cash ratio to be less than %f but is %f" % (b.id_, cr, thisCr))

    def test_banks_per_bank(self):
        self.simInfo.theParameters.set('loanSizeType', 'perBank')
        simulator.do_economy_parameters(self.simInfo, self.pList, self.parameterDefs)
        simulator.do_bank_parameters(self.simInfo, self.pList, self.parameterDefs)
        simulator.reset_economies(self.simInfo)
        simulator.reset_banks(self.simInfo)
        b1 = self.simInfo.bankDirectory["bank1"]
        b2 = self.simInfo.bankDirectory["bank2"]
        b3 = self.simInfo.bankDirectory["bank3"]

        # expect the following bank loans to be in place:
        # bank1 -> bank2, total size 10
        # bank2 -> bank1, } total size 20
        # bank2 -> bank3, }
        # bank3 -> bank1, total size 30

        for bFrom, bTo, bl in zip([b1, b2, b2, b3], [b2, b1, b3, b1], [10, 10, 10, 30]):
            lending = network.bank_lending(self.simInfo, bFrom, bTo)
            assert abs(bl - lending) < 10, ("expected lending from %s to %s to be roughly %r but is %r" %
                                            (bFrom.id_, bTo.id_, bl, lending))
            borrowing = network.bank_borrowing(self.simInfo, bTo, bFrom)
            assert abs(bl - borrowing) < 10, ("expected borrowing to %s from %s to be roughly %r but is %r" %
                                              (bTo.id_, bFrom.id_, bl, borrowing))

