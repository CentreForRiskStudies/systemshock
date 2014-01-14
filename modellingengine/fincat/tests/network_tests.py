__author__ = 'Louise'

from nose.tools import eq_, raises
import FinCat.network as network
from utils import approx_equal, setup_banks1
from FinCat.utils import ProportionError


class TestNetwork:
    def setUp(self):

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

    def test_banks1(self):

        for b, inv in zip(range(5), [50, 20, 40, 30, 80]):
            iv = self.banks[b].investment_value()
            eq_(inv, iv, "Bank %r inv value should be %r but is %r (1)" % (b, inv, iv))

        for b, l in zip(range(5), [10, 10, 20, 30, 40]):
            bl = network.bank_lending(self.simInfo, self.banks[b])
            eq_(l, bl, "Bank %r lending should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [0, 1, 2, 3, 4]):
            bl = network.bank_lending(self.simInfo, self.banks[0], self.banks[b])
            eq_(l, bl, "Bank0 lending to %r should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [100, 1, 2, 3, 4]):
            bl = network.bank_borrowing(self.simInfo, self.banks[b])
            eq_(l, bl, "Bank %r borrowing should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [0, 10, 20, 30, 40]):
            bl = network.bank_borrowing(self.simInfo, self.banks[0], self.banks[b])
            eq_(l, bl, "Bank0 borrowing from %r should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [110, 21, 32, 43, 54]):
            bl = self.banks[b].total_liabilities()
            eq_(l, bl, "Bank %r liabilities should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [110, 50, 75, 70, 125]):
            bl = self.banks[b].total_assets()
            eq_(l, bl, "Bank %r assets should be %r but is %r (1)" % (b, l, bl))

        for b, l in zip(range(5), [0, 29, 43, 27, 71]):
            bl = self.banks[b].equity_value()
            eq_(l, bl, "Bank %r equity should be %r but is %r (1)" % (b, l, bl))

        self.simInfo.updateCount = 6
        for b, d, c in zip(range(5), [9, 18, 27, 36, 45], [49, 18, 12, 6, 0]):
            self.banks[b].withdraw_deposits(0.1)
            dep = self.banks[b].deposits
            cash = self.banks[b].cash
            eq_(d, dep, "Bank %r deposits should be %r but is %r (1)" % (b, d, dep))
            eq_(c, cash, "Bank %r cash should be %r but is %r (1)" % (b, c, cash))

        for b, l in zip(range(5), [0, 29, 43, 27, 71]):
            bl = self.banks[b].equity_value()
            eq_(l, bl, "Bank %r equity should be %r but is %r (2)" % (b, l, bl))

    @raises(ProportionError)
    def test_withdraw_wrong(self):
        self.banks[1].withdraw_deposits(5)

    def test_lending(self):

        #  check individual loans between the banks in both directions
        for b, l, factor in zip(range(5), [10, 10, 20, 30, 40], [.5, 0, .1, .6, .8]):
            thisBank = self.banks[b]
            thisBank.parameters.set('loanShockFactor', factor)
            # used later...

            bl = network.bank_lending(self.simInfo, self.banks[b])
            eq_(l, bl, "Bank %r lending should be %r but is %r (mat1)" % (b, l, bl))
            if b != 0:
                lHistory0 = self.banks[0].borrowingHistory[thisBank]
                # should have only initial setup in
                eq_(len(lHistory0), 1,
                    "expected loan history from %r to 0 to have 1 entry but got %r" % (b, len(lHistory0)))
                when, amount = lHistory0[0]
                eq_(when, 0, "expected last loan history item from %r to 0 to be at time 0 but got %r" % (b, when))
                eq_(amount, l,
                    "expected last loan history item from %r to 0 to be amount %r but got %r" % (b, l, amount))
        for b, l in zip(range(5), [100, 1, 2, 3, 4]):
            thisBank = self.banks[b]
            bl = network.bank_borrowing(self.simInfo, self.banks[b])
            eq_(l, bl, "Bank %r borrowing should be %r but is %r (mat2)" % (b, l, bl))
            lHistory = thisBank.borrowingHistory
            if b == 0:
                eq_(len(lHistory), 4, "expected loan history for %r to have length 4 but got %r" % (b, len(lHistory)))
            else:
                eq_(len(lHistory), 1, "expected loan history for %r to have length 1 but got %r" % (b, len(lHistory)))
                lHistory0 = lHistory[self.banks[0]]
                eq_(len(lHistory0), 1,
                    "expected loan history from 0 to %r to have 1 entry but got %r" % (b, len(lHistory0)))
                when, amount = lHistory0[0]
                eq_(when, 0, "expected last loan history item from 0 to %r to be at time 0 but got %r" % (b, when))
                eq_(amount, l,
                    "expected last loan history item from 0 to %r to be amount %r but got %r" % (b, l, amount))

        self.simInfo.updateCount = 2
        for bank in self.banks:
            bank.do_loan_shock()

        for b, l in zip(range(5), [4.8, 5, 10, 15, 20]):
            thisBank = self.banks[b]
            bl = network.bank_lending(self.simInfo, self.banks[b])
            assert approx_equal(l, bl, 0.000001), "Bank %r lending should be %r but is %r (mat3)" % (b, l, bl)
            if b != 0:
                lHistory0 = self.banks[0].borrowingHistory[thisBank]
                # should have initial setup plus loan maturities
                eq_(len(lHistory0), 2,
                    "expected loan history from %r to 0 to have 2 entries but got %r" % (b, len(lHistory0)))
                when, amount = lHistory0[1]
                eq_(when, 2, "expected last loan history item from %r to 0 to be at time 2 but got %r" % (b, when))
                eq_(amount, l,
                    "expected last loan history item from %r to 0 to be amount %r but got %r" % (b, l, amount))

        for b, l in zip(range(5), [50, 1, 1.8, 1.2, .8]):
            thisBank = self.banks[b]
            bl = network.bank_borrowing(self.simInfo, self.banks[b])
            assert approx_equal(l, bl, 0.0000001), "Bank %r borrowing should be %r but is %r (mat4)" % (b, l, bl)
            lHistory = thisBank.borrowingHistory
            if b == 0:
                eq_(len(lHistory), 4, "expected loan history for %r to have length 4 but got %r" % (b, len(lHistory)))
            else:
                eq_(len(lHistory), 1, "expected loan history for %r to have length 1 but got %r" % (b, len(lHistory)))
                lHistory0 = lHistory[self.banks[0]]  # history of borrowing from bank0
                if b == 1:
                    # factor for bank 1 is 0, so nothing happens
                    lhLen = 1
                    lhWhen = 0
                else:
                    lhLen = 2
                    lhWhen = 2
                eq_(len(lHistory0), lhLen,
                    "expected loan history from 0 to %r to have %r entries but got %r" % (b, lhLen, len(lHistory0)))
                when, amount = lHistory0[lhLen - 1]
                eq_(when, lhWhen,
                    "expected last loan history item from 0 to %r to be at time %s but got %r" % (b, lhWhen, when))
                assert approx_equal(amount, l, 0.0000001), (
                    "expected last loan history item from 0 to %r to be amount %r but got %r" % (
                    b, l, amount))

        # orig cash: 50 20 15 10 5
        for b, l in zip(range(5), [5.2, 25, 24.8, 23.2, 21.8]):
            bank = self.banks[b]
            bl = bank.cash
            assert approx_equal(l, bl, 0.0000001), "Bank %r cash should be %r but is %r (mat5)" % (b, l, bl)

        # orig liabilities: 110, 21, 32, 43, 54
        for b, l in zip(range(5), [60, 21, 31.8, 41.2, 50.8]):
            bank = self.banks[b]
            bl = bank.total_liabilities()
            eq_(l, bl, "Bank %r liabilities should be %r but is %r (mat6)" % (b, l, bl))

        # orig assets: 110, 50, 75, 70, 125
        for b, l in zip(range(5), [60, 50, 74.8, 68.2, 121.8]):
            bank = self.banks[b]
            bl = bank.total_assets()
            eq_(l, bl, "Bank %r assets should be %r but is %r (mat7)" % (b, l, bl))

        # equity value hasn't changed, as loans have just been swapped for cash
        for b, l in zip(range(5), [0, 29, 43, 27, 71]):
            bank = self.banks[b]
            bl = bank.equity_value()
            eq_(l, bl, "Bank %r equity should be %r but is %r (mat8)" % (b, l, bl))

    def test_default_bank(self):

        self.banks[1].cash = -10
        # this sends it insolvent
        # with assets 20 and liabilities 21
        self.banks[1].check_solvency()
        prop = 20.0 / 21.0

        self.simInfo.updateCount = 2
        affected = network.do_default_loans(self.simInfo, self.banks[1], prop)

        eq_(1, len(affected), "1 bank should be affected, but %r are" % len(affected))
        assert self.banks[0] in affected, "Bank 0 should be affected but isn't"
        # 0 had lent 1 1, and borrowed 10
        # orig bank lending and borrowing:
        # lending:   0  10, 1 10, 2 20, 3 30, 4 40
        # borrowing: 0 100, 1  1, 2  2, 3  3, 4  4
        bl = network.bank_lending(self.simInfo, self.banks[1])
        assert approx_equal(10, bl, 0.0000001), "Bank %r lending should be %r but is %r (def1)" % (0, 10, bl)
        # the lending has been netted off...
        bl = network.bank_borrowing(self.simInfo, (self.banks[1]))
        assert approx_equal(prop, bl, 0.0000001), "Bank %r lending should be %r but is %r (def2)" % (0, prop, bl)

        eq_(1, len(affected), "1 banks should be affected, but %r are" % len(affected))
