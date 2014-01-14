__author__ = 'Louise'

from nose.tools import eq_, raises
from utils import approx_equal, setup_banks1
from FinCat.utils import ProportionError, UniqueError
from FinCat.bank import Bank


class TestBank:
    def setUp(self):
        self.banks, self.econ, self.simInfo = setup_banks1()
        # gives 5 banks with the following:
        # total investments: 0  50, 1 20, 2 40, 3 30, 4  80
        # lending:           0  10, 1 10, 2 20, 3 30, 4  40
        # cash:              0  50, 1 20, 2 15, 3 10, 4   5
        # deposits:          0  10, 1 20, 2 30, 3 40, 4  50
        # borrowing:         0 100, 1  1, 2  2, 3  3, 4   4
        # liabilities:       0 110, 1 21, 2 32, 3 43, 4  54
        # assets:            0 110, 1 50, 2 75, 3 70, 4 125
        # capital:           0   0, 1 29, 2 43, 3 27, 4  71

    def test_create1(self):
        eq_(len(self.simInfo.bankDirectory), 5, "expected 5 banks in the directory but got %r" % len(self.simInfo.bankDirectory))
        b = self.simInfo.bankDirectory["bank1"]
        eq_(b, self.banks[1], "expected banks to be the same")
        assert b != self.banks[0], "expected banks to be different"

    @raises(UniqueError)
    def test_create2(self):
        Bank(self.simInfo, "bank0", self.econ, self.econ.params)

    def test_reduce_inv(self):
        self.econ.params.set('fireSaleFactor', 0.0)

        investments = self.banks[0].get_investments()
        eq_(1, len(investments), "expected bank 0 to have one investment but has %r" % investments)
        self.simInfo.updateCount = 1
        self.banks[0].reduce_investments(0.5)
        # no other banks have investments in common with bank 0
        affected = self.banks[0].get_sharing_banks()
        eq_(0, len(affected), "Expected no banks to be affected but found %r (1)" % len(affected))
        iVal = self.banks[0].investment_value()
        assert approx_equal(25, iVal, 0.00001), "expected bank 0 to have investments of 25 but has %r (2)" % iVal

        investments = self.banks[1].get_investments()
        eq_(2, len(investments), "expected bank 1 to have 2 investments but has %r" % investments)
        self.simInfo.updateCount = 2
        self.banks[1].reduce_investments(0.5)
        affected = self.banks[1].get_sharing_banks()
        eq_(3, len(affected), "expected bank 1 to affect 3 banks but affects %r" % len(affected))
        iVal = self.banks[1].investment_value()
        assert approx_equal(10, iVal, 0.00001), "expected bank 1 to have investments of 10 but has %r (2)" % iVal

    @raises(ProportionError)
    def test_reduce_inv_wrong(self):
        self.banks[3].reduce_investments(-3)

    def test_liquidise(self):
        self.econ.params.set('fireSaleFactor', 0.0)

        self.banks[0].cash = -10
        self.simInfo.updateCount = 3
        affected = self.banks[0].liquidise(0.0, 1.0)
        # Should have needed to sell off 10 in investments
        eq_(0, len(affected), "Expected no banks to be affected but found %r (liq1)" % len(affected))
        iVal = self.banks[0].investment_value()
        bCash = self.banks[0].cash
        assert approx_equal(40, iVal, 0.00001), "expected bank 0 to have investments of 40 but has %r (liq1)" % iVal
        assert approx_equal(0, bCash, 0.000001), "expected bank 0 to have zero cash but has %f (liq1)" % bCash

        self.simInfo.updateCount = 5
        affected = self.banks[4].liquidise(.1, 1.0)
        # should take investments down to 72.5
        eq_(3, len(affected), "Expected 3 banks to be affected but found %r (liq2)" % len(affected))
        iVal = self.banks[4].investment_value()
        bCash = self.banks[4].cash
        assert approx_equal(72.5, iVal, 0.00001), "expected bank 4 to have investments of 72.5 but has %r (liq2)" % iVal
        assert approx_equal(12.5, bCash, 0.000001), "expected bank 4 to have 12.5 cash but has %f (liq2)" % bCash

        self.simInfo.updateCount = 6
        affected = self.banks[2].liquidise(0, 1.0)
        # should have no effect
        eq_(0, len(affected), "Expected no banks to be affected but found %r (liq3)" % len(affected))
        iVal = self.banks[2].investment_value()
        bCash = self.banks[2].cash
        assert approx_equal(40, iVal, 0.00001), "expected bank 2 to have investments of 40 but has %r (liq3)" % iVal
        assert approx_equal(15, bCash, 0.000001), "expected bank 2 to have 15 cash but has %f (liq3)" % bCash

        self.banks[2].cash = -10  # takes actual assets to 60, net assets to 50
        self.simInfo.updateCount = 7
        affected = self.banks[2].liquidise(0.1, 1.0)
        # should end up with 6 cash, having sold 16 investments
        eq_(3, len(affected), "Expected 3 banks to be affected but found %r (liq4)" % len(affected))
        iVal = self.banks[2].investment_value()
        bCash = self.banks[2].cash
        assert approx_equal(24, iVal, 0.00001), "expected bank 2 to have investments of 24 but has %r (liq4)" % iVal
        assert approx_equal(6, bCash, 0.0000001), "expected bank 2 to have 6 cash but has %f (liq4)" % bCash

        # we expect to run out of investments on this one
        self.simInfo.updateCount = 8
        affected = self.banks[1].liquidise(0.9, 1.0)
        ta = self.banks[1].total_assets()
        iv = self.banks[1].investment_value()
        bCash = self.banks[1].cash
        assert bCash < 0.9 * ta, "expected less than %f cash, but got %f" % (0.9 * ta, bCash)
        assert approx_equal(0, iv, 0.00001), "expected zero investments but got %f" % iv
        eq_(3, len(affected), "expected 3 banks to be affected but got %r (liq4.5)" % len(affected))
        affected = self.banks[1].get_sharing_banks()
        eq_(0, len(affected), "expected 0 sharing banks  but got %r (liq4.5)" % len(affected))

        self.econ.params.set('fireSaleFactor', 1.0)  # price falls on sales
        self.simInfo.updateCount = 9
        self.banks[3].liquidise(0.2, 1.1)
        # total assets will fall, because of sales
        ta = self.banks[3].total_assets()
        bCash = self.banks[3].cash
        assert ta < 70, "expected total assets < 70 but is %f (liq5)" % ta
        assert bCash >= 0.2 * ta, "expected cash >= %f but is %f (liq5)" % (0.2 * ta, bCash)

    def test_update1(self):
        self.econ.params.set('targetCashProportion', 0.0)
        self.econ.params.set('assetSalesFactor', 1.0)

        self.banks[0].cash = -10
        self.banks[0].check_solvency()
        assert not self.banks[0].solvent, "expected bank to be insolvent!! (up1)"
        self.simInfo.updateCount = 1
        affected, ratio = self.banks[0].update()
        # assets = 50 (with -10 cash), liabilities 110
        # so liabilities reduced to 5/11 of original
        prop = 5.0 / 11.0

        # it has borrowed from 4 other banks...
        eq_(4, len(affected), "Expected 4 banks to be affected but found %r (up1)" % len(affected))
        for b, bl in zip([1, 2, 3, 4], [10, 20, 30, 40]):
            lHistory = self.banks[0].borrowingHistory[self.banks[b]]
            thisB = self.banks[b].id_
            # expect 2 entries in each history, one from when the loan was set up and one from the update
            eq_(2, len(lHistory), "expected 2 entries in the loan history for %s but got %r" % (thisB, len(lHistory)))
            when, amount = lHistory[1]  # last entry
            eq_(1, when, "expected last entry in loan history for %s to be 1, but was %r" % (thisB, when))
            assert approx_equal(amount, prop * bl,
                                0.0000001), "expected last loan history amount for %s to be %f, but got %f" % (
                thisB, prop * bl, amount)
            when, amount = lHistory[0]  # first entry
            eq_(0, when, "expected first entry in loan history for %s to be 0, but was %r" % (thisB, when))
            assert approx_equal(amount, bl,
                                0.00000001), "expected first loan history amount for %s to be %f, but got %f" % (
                thisB, bl, amount)

        # Insolvent, so nothing is done about its liquidity
        iVal = self.banks[0].investment_value()
        assert approx_equal(50, iVal, 0.00001), "expected bank 0 to have investments of 50 but has %r (up1)" % iVal
        assert approx_equal(-10, self.banks[0].cash,
                            "expected bank 0 to have -10 cash but has %f (up1)" % self.banks[0].cash)
        # but it should have defaulted on its liabilities
        dHistory = self.banks[0].defaultHistory
        eq_(len(dHistory), 1, "expected an entry in the default history but got %r" % len(dHistory))

        liabilities = self.banks[0].total_liabilities()
        assert approx_equal(50, liabilities, .0000001), "Expected total liabilities to be 50 but got %f" % liabilities
        deposits = self.banks[0].deposits
        assert approx_equal(prop * 10, deposits, .00000001), "Expected deposits to be %f but got %f" % (prop * 10, deposits)
        capital = self.banks[0].equity_value()
        assert approx_equal(0, capital, 0.00000001), "Expected zero capital but got %f" % capital

        # it has been updated, so should have a history entry
        hLen = len(self.banks[0].stateHistory)
        eq_(hLen, 1, "expected 1 entry in state history but got %r" % hLen)

    def test_update2(self):
        self.econ.params.set('targetCashProportion', 0.2)
        self.econ.params.set('assetSalesFactor', 1.0)

        self.simInfo.updateCount = 1
        affected, ratio = self.banks[4].update()
        # has enough investments to sell
        eq_(3, len(affected), "Expected 3 banks to be affected but found %r (up2)" % len(affected))
        assert self.banks[4].solvent, "expected bank to be solvent!! (up2)"
        assert self.banks[4].liquid, "expected bank to be liquid!! (up2)"

        b3 = self.banks[3]
        b3.deposits = 10.0
        b3.cash = -40
        # doesn't have enough investments, but is solvent
        # b3 shares inv3 with banks 1 2 and 4
        self.simInfo.updateCount = 2
        affected, ratio = b3.update()
        assert b3.solvent, "expected bank to be solvent!! (up3)"
        assert not b3.liquid, "expected bank to be illiquid!! (up3)"
        eq_(3, len(affected), "Expected 3 banks to be affected but found %r (up3)" % len(affected))

    def test_updated3(self):
        self.econ.params.set('targetCashProportion', 0.0)
        self.econ.params.set('assetSalesFactor', 1.0)

        self.banks[1].cash = -35
        # this sends the assets negative, so the liabilities will be a total write off
        self.banks[1].check_solvency()
        self.simInfo.updateCount = 2
        affected, ratio = self.banks[1].update()
        borrowing = self.banks[1].total_borrowing()
        eq_(0, borrowing, "expected zero borrowing but got %f" % borrowing)
        eq_(0, self.banks[1].deposits, "expected zero deposits but got %f" % self.banks[1].deposits)
        eq_(1, len(affected), "Expected 1 banks to be affected but found %r (up4)" % len(affected))

        sHistory = self.banks[1].stateHistory
        when, bName, lending, investments, cash, borrowing, deposits, capital = sHistory[-1]
        eq_(2, when, "expected state history item at time 2 but got %r" % when)
        eq_(0, borrowing, "expected zero borrowing in state history but got %f" % borrowing)
        eq_(0, deposits, "expected zero deposits in state history but got %f" % deposits)
        balance = lending + investments + cash - borrowing - deposits - capital
        eq_(0, balance, "expected zero balance in state history but got %f" % balance)

    def test_deposit_shock(self):
        for b, d, c, f in zip(range(5), [10, 20, 30, 40, 50], [50, 20, 15, 10, 5], [.1, .2, .3, .4, .5]):
            bank = self.banks[b]
            bank.parameters.set('depositShockFactor', f)
            assert approx_equal(d, bank.deposits, 0.0000001), "expected bank %s to have %r deposits but got %r" % (b, d, bank.deposits)
            assert approx_equal(c, bank.cash, 0.0000001), "expected bank %s to have %r cash but got %r" % (b, c, bank.cash)
        for b, d, c in zip(range(5), [9, 16, 21, 24, 25], [49, 16, 6, -6, -20]):
            bank = self.banks[b]
            bank.do_deposit_shock()
            assert approx_equal(d, bank.deposits, 0.0000001), "expected bank %s to have %r deposits but got %r" % (b, d, bank.deposits)
            assert approx_equal(c, bank.cash, 0.0000001), "expected bank %s to have %r cash but got %r" % (b, c, bank.cash)

    def test_history(self):
        thisBank = self.banks[0]
        self.simInfo.updateCount = 4
        thisBank.record_state()
        self.simInfo.updateCount = 6
        thisBank.record_state()   # nothing has changed so shouldn't be added...
        l1 = len(thisBank.stateHistory)
        eq_(l1, 1, "expected one item in state history but got %r" % l1)
        lastWhen = thisBank.stateHistory[-1][0]
        eq_(lastWhen, 4, "expected last item to be at count 4 but was %r" % lastWhen)
        thisBank.cash = 45
        self.simInfo.updateCount = 7
        thisBank.record_state()   # this one should be added as cash has changed
        l1 = len(thisBank.stateHistory)
        eq_(l1, 2, "expected 2 items in state history but got %r" % l1)
        lastWhen = thisBank.stateHistory[-1][0]
        eq_(lastWhen, 7, "expected last item to be at count 7 but was %r" % lastWhen)


