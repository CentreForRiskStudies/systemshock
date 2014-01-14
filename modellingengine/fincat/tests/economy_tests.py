__author__ = 'Louise'

from nose.tools import eq_, raises

from FinCat.economy import Economy
import FinCat.network as network
from utils import check_asset_network, check_asset_totals, check_asset_holding, approx_equal, setup_banks1
from FinCat.utils import UniqueError, Parameters, ProportionError, SimulationInfo
import FinCat.simulator as simulator


class TestEconomy:
    def setup(self):
        self.simInfo = SimulationInfo()

    def test_economy_create(self):
        econ1 = Economy(self.simInfo, "Economy1")
        eq_(econ1.id_, "Economy1")
        eq_(len(self.simInfo.economyDirectory), 1, "expected 1 economy but got %r" % len(self.simInfo.economyDirectory))
        econ2 = Economy(self.simInfo, "Economy2")
        eq_(econ2.id_, "Economy2")
        eq_(len(self.simInfo.economyDirectory), 2, "expected 2 economies but got %r" % len(self.simInfo.economyDirectory))
        econ = self.simInfo.economyDirectory["Economy1"]
        eq_(econ, econ1, "Expected economies to be the same")
        assert econ != econ2, "Expected economies to be different"

    @raises(UniqueError)
    def test_economy_create2(self):
        Economy(self.simInfo, "e1")
        Economy(self.simInfo, "e1")

    def test_investment_create(self):
        econ = Economy(self.simInfo, "Economy1")
        newI = econ.create_investment()
        eq_(newI.id_, "Economy1-inv0", "Expected investment to have name %r but is %r" % ("Economy1-inv0", newI.id_))
        eq_(1, len(econ.investments), "expected one investment but got %r" % len(econ.investments))
        inv = econ.investments[0]
        eq_(newI, inv, "expected the same investment")
        eq_(econ, inv.economy, "should be in this economy")
        check_asset_network(self.simInfo, 1, 0, "inv1")
        self.simInfo.updateCount = 1
        econ.create_investment()
        check_asset_network(self.simInfo, 2, 0, "inv2")
        eq_(2, len(econ.investments), "expected 2 investments but got %r" % len(econ.investments))
        self.simInfo.updateCount = 2
        econ.create_investments(5)
        eq_(7, len(econ.investments), "expected 7 investments but got %r" % len(econ.investments))
        check_asset_network(self.simInfo, 7, 0, "inv3")

    def test_investments_buy1(self):
        parameterDefs = simulator.define_parameters()
        eParams = Parameters(parameterDefs)
        econ = Economy(self.simInfo, "Economy1", eParams)
        newI = econ.create_investment()

        hLen = len(newI.priceHistory)
        self.simInfo.updateCount = 1
        newI.set_price(1.0)
        hLen1 = len(newI.priceHistory)
        eq_(hLen + 1, hLen1, "expected %r items in price history but got %r" % (hLen + 1, hLen1))
        when, price = newI.priceHistory[hLen1 - 1]
        eq_(1, when, "expected last item in price history to be at time 0 but was %r" % when)
        eq_(1.0, price, "expected last price in price history to be 1.0 but was %r" % price)

        self.simInfo.updateCount = 2
        q, v = newI.buy(1, "buyer1")
        eq_(q, 1, "expected quantity 1 but got %r (1)" % q)
        eq_(v, 1, "expected consideration 1 but got %r (1)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="buy1")
        check_asset_holding(newI, "buyer1", 1, 1.0, tag="buy1")
        check_asset_totals(self.simInfo, newI, 1, 1.0, "buy1")
        hHistory = newI.holdingHistory["buyer1"]
        eq_(1, len(hHistory), "expected 1 item in holding history but got %r" % len(hHistory))
        when, amount = hHistory[-1]
        eq_(2, when, "expected last item in holding history to be at time 1 but got %r" % when)
        eq_(1, amount, "expected last item in holding history to be amount 1 but got %r" % amount)

        self.simInfo.updateCount = 3
        newI.set_price(2.0)
        q, v = newI.buy(3, "buyer1")
        eq_(q, 3, "expected quantity 3 but got %r (2)" % q)
        eq_(v, 6, "expected consideration 6 but got %r (2)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="buy1")
        check_asset_holding(newI, "buyer1", 4, 8.0, tag="buy2")
        check_asset_totals(self.simInfo, newI, 4, 2.0, tag="buy2")

        eq_(newI.value("buyer2"), 0, "expected buyer2 value to be 0 but is %r" % newI.value("buyer2"))
        eq_(newI.quantity("buyer2"), 0, "expected buyer2 quantity to be 0 but is %r" % newI.quantity("buyer2"))

        # now sell some
        self.simInfo.updateCount = 4
        newI.set_price(5.0)
        econ.params.set('fireSaleFactor', 0.0)  # selling has no effect on price
        q, v = newI.sell(3, "buyer1")
        eq_(q, 3, "expected quantity 3 but got %r (4)" % q)
        eq_(v, 15, "expected consideration 15 but got %r (4)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="sell1")
        check_asset_holding(newI, "buyer1", 1, 5.0, "sell1")
        check_asset_totals(self.simInfo, newI, 1, 5.0, "sell1")

        self.simInfo.updateCount = 5
        q, v = newI.sell(1, "buyer2")
        eq_(q, 0, "expected quantity 0 but got %r" % q)
        eq_(v, 0, "expected consideration 0 but got %r" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="sell2")
        check_asset_holding(newI, "buyer1", 1, 5.0, "sell2")
        check_asset_totals(self.simInfo, newI, 1, 5.0, "sell2")

        self.simInfo.updateCount = 6
        q, v = newI.sell(-6, "buyer1")
        eq_(q, 0, "expected quantity 0 but got %r (4.5)" % q)
        eq_(v, 0, "expected consideration 0 but got %r (4.5)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="sell3")
        check_asset_holding(newI, "buyer1", 1, 5.0, "sell3")
        check_asset_totals(self.simInfo, newI, 1, 5.0, "sell3")

        pHistory = newI.priceHistory
        when, price = pHistory[-1]
        eq_(4, when, "expected last item in price history to be at time 4 but got %r" % when)
        eq_(5.0, price, "expected last item in price history to be price 5 but got %r" % price)

        self.simInfo.updateCount = 7
        newI.set_price(3)
        q, v = newI.sell(5, "buyer1")
        eq_(q, 1, "expected quantity 1 but got %r (5)" % q)
        eq_(v, 3, "expected consideration 3 but got %r (5)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=0, tag="sell4")
        check_asset_holding(newI, "buyer1", 0, 0, "sell4")
        check_asset_totals(self.simInfo, newI, 0, 3, "sell4")

        self.simInfo.updateCount = 8
        q, v = newI.buy(-6, "buyer1")
        eq_(q, 0, "expected quantity 0 but got %r (6)" % q)
        eq_(v, 0, "expected consideration 0 but got %r (6)" % v)

        hHistory = newI.holdingHistory["buyer1"]
        when, amount = hHistory[-1]
        eq_(7, when, "expected last item in holding history to be at time 7 but got %r" % when)
        eq_(0.0, amount, "expected last item in holding history to be amount 0 but got %r" % amount)

        pHistory = newI.priceHistory
        when, price = pHistory[-1]
        eq_(7, when, "expected last item in price history to be at time 7 but got %r" % when)
        eq_(3.0, price, "expected last item in price history to be price 3 but got %r" % price)

    def test_investments_buy2(self):
        parameterDefs = simulator.define_parameters()
        eParams = Parameters(parameterDefs)
        econ = Economy(self.simInfo, "Economy1", eParams)
        newI = econ.create_investment()
        econ.params.set('fireSaleFactor', 0.0)

        self.simInfo.updateCount = 1
        newI.set_price(2)
        q, v = newI.buy(3, "buyer1")
        eq_(q, 3, "expected quantity 3 but got %r (1)" % q)
        eq_(v, 6, "expected consideration 6 but got %r (1)" % v)
        check_asset_network(self.simInfo, nodes=2, edges=1, tag="buy3")
        check_asset_holding(newI, "buyer1", quantity=3, value=6, tag="buy3")
        check_asset_totals(self.simInfo, newI, 3, 2, tag="buy3")

        self.simInfo.updateCount = 2
        q, v = newI.buy(4, "buyer2")
        eq_(q, 4, "expected quantity 4 but got %r (2)" % q)
        eq_(v, 8, "expected consideration 8 but got %r (2)" % v)
        check_asset_network(self.simInfo, nodes=3, edges=2, tag="buy4")
        check_asset_holding(newI, "buyer1", quantity=3, value=6, tag="buy4")
        check_asset_holding(newI, "buyer2", quantity=4, value=8, tag="buy4")
        check_asset_totals(self.simInfo, newI, 7, 2, tag="buy4")

        self.simInfo.updateCount = 3
        q, v = newI.buy(2, "buyer3")
        eq_(q, 2, "expected quantity 2 but got %r (3)" % q)
        eq_(v, 4, "expected consideration 4 but got %r (3)" % v)
        check_asset_network(self.simInfo, nodes=4, edges=3, tag="buy5")
        check_asset_holding(newI, "buyer1", quantity=3, value=6, tag="buy5")
        check_asset_holding(newI, "buyer2", quantity=4, value=8, tag="buy5")
        check_asset_holding(newI, "buyer3", quantity=2, value=4, tag="buy5")
        check_asset_totals(self.simInfo, newI, 9, 2, tag="buy3")

        self.simInfo.updateCount = 4
        q, v = newI.sell(5, "buyer2")
        eq_(q, 4, "expected quantity 4 but got %r (4)" % q)
        eq_(v, 8, "expected consideration 8 but got %r (4)" % v)
        check_asset_network(self.simInfo, nodes=4, edges=2, tag="buy5")
        check_asset_holding(newI, "buyer1", quantity=3, value=6, tag="buy5")
        check_asset_holding(newI, "buyer2", quantity=0, value=0, tag="buy5")
        check_asset_holding(newI, "buyer3", quantity=2, value=4, tag="buy5")
        check_asset_totals(self.simInfo, newI, 5, 2, tag="buy3")

    def test_firesale(self):
        parameterDefs = simulator.define_parameters()
        eParams = Parameters(parameterDefs)
        simInfo = SimulationInfo()

        econ = Economy(simInfo, "Economy1", eParams)
        inv = []
        holders = []
        for i in range(5):
            inv.append(econ.create_investment())
            holders.append("holder%s" % i)
        econ.params.set('fireSaleFactor', 1.0)  # price is affected by sales
        simInfo.updateCount = 1
        for i in range(5):
            inv[0].buy(5, holders[i])
            inv[1].buy(5, holders[i])

        # one holder sells a bit of the investment
        simInfo.updateCount = 2
        q, v = inv[0].sell(1, holders[0])
        assert v < 1, "expected consideration < 1 but is %f" % v
        eq_(v, inv[0].currentPrice,
            "expected consideration equal to price but they are %f, %f" % (v, inv[0].currentPrice))
        check_asset_holding(inv[0], holders[0], quantity=4, value=4 * v, tag="fs1")
        check_asset_holding(inv[0], holders[1], quantity=5, value=5 * v, tag="fs1")
        price1 = inv[0].currentPrice

        simInfo.updateCount = 3
        q, v = inv[0].sell(3, holders[2])  # a total of 4 has now been sold
        price2 = inv[0].currentPrice
        assert price2 < price1, "expected price < %f but is %f (fs2)" % (price1, price2)
        assert approx_equal(v, price2 * q, 0.00001), "expected consideration %f but is %f (fs2)" % (price2 * q, v)

        simInfo.updateCount = 4
        inv[1].sell(4, holders[3])  # sell 4, so price should be same as inv0
        price3 = inv[1].currentPrice
        assert approx_equal(price2, price3, 0.00001), "expected price to be %f but is %f (fs3)" % (price2, price3)

        pHistory = inv[1].priceHistory
        when, price = pHistory[-1]
        eq_(4, when, "expected last item in price history to be at time 4 but got %r" % when)
        eq_(price3, price, "expected last item in price history to be price %f but got %f" % (price3, price))

    def test_revalue(self):
        econ1 = Economy(self.simInfo, "Economy1")
        econ2 = Economy(self.simInfo, "Economy2")
        inv = []
        for i in range(5):
            inv.append(econ1.create_investment())
            inv.append(econ2.create_investment())

        self.simInfo.updateCount = 1
        econ1.revalue_investments(1.5)
        for i in range(5):
            eq_(1.5, inv[i * 2].currentPrice,
                "expected current price to be 1.5 but was %f for %r" % (inv[i * 2].currentPrice, i * 2))
            eq_(1, inv[i * 2 + 1].currentPrice,
                "expected current price to be 1.0 but was %f for %r" % (inv[i * 2 + 1].currentPrice, i * 2 + 1))

        self.simInfo.updateCount = 2
        inv[1].set_price(20)
        econ2.revalue_investments(.1)
        eq_(2, inv[1].currentPrice, "expected current price to be 2, but was %f" % inv[1].currentPrice)
        pHistory = inv[1].priceHistory
        when, price = pHistory[-1]
        eq_(2, when, "expected last item in price history to be at time 2 but got %r" % when)
        eq_(2, price, "expected last item in price history to be price 2 but got %f" % price)

    def test_deposit_withdrawals(self):
        self.banks, self.econ, self.simInfo = setup_banks1()
        # gives 5 banks with the following:
        # total investments: 0  50, 1 20, 2 40, 3 30, 4  80
        # lending:           0  10, 1 10, 2 20, 3 30, 4  40
        # borrowing:         0 100, 1  1, 2  2, 3  3, 4   4
        # cash:              0  50, 1 20, 2 15, 3 10, 4   5
        # deposits:          0  10, 1 20, 2 30, 3 40, 4  50
        # liabilities:       0 110, 1 21, 2 32, 3 43, 4  54
        # assets:            0 110, 1 50, 2 75, 3 70, 4 125
        # capital:           0   0, 1 29, 2 43, 3 27, 4  71

        self.simInfo.updateCount = 2
        self.econ.do_deposit_withdrawals(0.2)
        for b, d, c in zip(range(5), [8, 16, 24, 32, 40], [48, 16, 9, 2, -5]):
            dep = self.banks[b].deposits
            cash = self.banks[b].cash
            eq_(d, dep, "Bank %r deposits should be %r but is %r (1)" % (b, d, dep))
            eq_(c, cash, "Bank %r cash should be %r but is %r (1)" % (b, c, cash))

    @raises(ProportionError)
    def test_withdraw_wrong2(self):
        self.banks, self.econ, self.simInfo= setup_banks1()
        self.simInfo.updateCount = 3
        self.econ.do_deposit_withdrawals(1.2)

    def test_investment_shock(self):
        parameterDefs = simulator.define_parameters()
        eParams = Parameters(parameterDefs)
        econ1 = Economy(self.simInfo, "Economy1", eParams)
        eParams = Parameters(parameterDefs)
        econ2 = Economy(self.simInfo, "Economy2", eParams)
        inv = []
        for i in range(10):
            inv.append(econ1.create_investment())
            inv.append(econ2.create_investment())

        econ1.params.set('investmentShockFactor', .5)
        econ1.params.set('investmentShockProportion', .8)
        self.simInfo.updateCount = 2
        victims = econ1.do_investment_shock()
        eq_(len(victims), 8, "expected 8 investments to be affected but got %r" % len(victims))
        for victim in victims:
            eq_(victim.currentPrice, 0.5,
                "expected price of %s to be .5 but got %f" % (victim.id_, victim.currentPrice))
        econ2.params.set('investmentShockFactor', .25)
        econ2.params.set('investmentShockProportion', .1)
        victims = econ2.do_investment_shock()
        eq_(len(victims), 1, "expected 1 investments to be affected but got %r" % len(victims))
        for victim in victims:
            eq_(victim.currentPrice, 0.75,
                "expected price of %s to be .75 but got %f" % (victim.id_, victim.currentPrice))
