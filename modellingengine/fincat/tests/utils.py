__author__ = 'Louise'

from nose.tools import eq_
import FinCat.network as network
from FinCat.bank import Bank
from FinCat.economy import Economy
from FinCat.utils import Parameters, SimulationInfo
import FinCat.simulator as simulator



def approx_equal(a, b, tol):
    if abs(a) == abs(b) == 0:
        ans = True
    else:
        diff = abs(a - b)
        ave = abs(a) + abs(b) / 2.0
        ans = diff / ave < tol
    return ans


def check_asset_network(simInfo, nodes, edges, tag):
    eq_(nodes, simInfo.assetNetwork.order(),
        "expected %r asset nodes but got %r (%s)" % (nodes, simInfo.assetNetwork.order(), tag))
    eq_(edges, simInfo.assetNetwork.size(),
        "expected %r asset edges but got %r (%s)" % (edges, simInfo.assetNetwork.size(), tag))


def check_asset_holding(inv, bank, quantity, value, tag):
    assert approx_equal(inv.quantity(bank), quantity, 0.0000001), \
        "expected holding of %f, but got %f (%s)" % (quantity, inv.quantity(bank), tag)
    assert approx_equal(inv.value(bank), value, 0.0000001), \
        "expected value of %f, but got %f (%s)" % (value, inv.value(bank), tag)


def check_asset_totals(simInfo, inv, quantity, price, tag):
    assert approx_equal(quantity, network.get_asset_volume(simInfo, inv), 0.0000001), \
        "expected volume of %f, but got %f (%s)" % (quantity, network.get_asset_volume(inv), tag)
    assert approx_equal(price, inv.currentPrice, 0.0000001), \
        "expected price of %f, but got %f (%s)" % (price, inv.currentPrice, tag)


def setup_banks1():
    simInfo = SimulationInfo()
    parameterDefs = simulator.define_parameters()
    eParams = Parameters(parameterDefs)

    banks = []
    econ = Economy(simInfo, "Economy1", eParams)

    for i in range(5):
        params = Parameters(parameterDefs, econ.params)
        banks.append(Bank(simInfo, "bank%s" % i, econ, params))

    econ.params.set('fireSaleFactor', 0.0)
    inv1 = econ.create_investment()
    inv2 = econ.create_investment()
    inv3 = econ.create_investment()
    inv1.buy(50, banks[0])
    inv2.buy(10, banks[1])
    inv2.buy(20, banks[2])
    inv2.buy(40, banks[4])
    inv3.buy(10, banks[1])
    inv3.buy(20, banks[2])
    inv3.buy(30, banks[3])
    inv3.buy(40, banks[4])
    # total investments: 0 50, 1 20, 2 40, 3 30, 4 80
    banks[0].add_loan(banks[1], amount=1)
    banks[0].add_loan(banks[2], amount=2)
    banks[0].add_loan(banks[3], amount=3)
    banks[0].add_loan(banks[4], amount=4)
    banks[1].add_loan(banks[0], amount=10)
    banks[2].add_loan(banks[0], amount=20)
    banks[3].add_loan(banks[0], amount=30)
    banks[4].add_loan(banks[0], amount=40)
    # lending:   0  10, 1 10, 2 20, 3 30, 4 40
    # borrowing: 0 100, 1  1, 2  2, 3  3, 4  4
    # matrix:  0   1   2   3   4
    #         10   0   0   0   0
    #         20   0   0   0   0
    #         30   0   0   0   0
    #         40   0   0   0   0
    banks[0].deposits = 10
    banks[1].deposits = 20
    banks[2].deposits = 30
    banks[3].deposits = 40
    banks[4].deposits = 50
    # liabilities: 0 110, 1 21, 2 32, 3 43, 4 54
    banks[0].cash = 50
    banks[1].cash = 20
    banks[2].cash = 15
    banks[3].cash = 10
    banks[4].cash = 5
    # assets:  0 110, 1 50, 2 75, 3 70, 4 125
    # capital: 0   0, 1 29, 2 43, 3 27, 4  71
    return banks, econ, simInfo
