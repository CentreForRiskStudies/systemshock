__author__ = 'Louise'

import math
import logging

import network
from utils import Parameters, UniqueError, get_diverse_sample, ProportionError, SimulationObject

logger = logging.getLogger("fc." + __name__)

# Things that are external to the financial network.


class Economy(SimulationObject):
    """
    Represents a grouping of things external to the financial system
    Every economy has a number of investments and banks.

    Attributes
        name
        banks
        investments
        params
    """

    def __init__(self, simInfo, name, params=None):
        """
        Initialise an economy with an empty list of banks and an empty list of investments
        """
        super(Economy, self).__init__(simInfo, name)

        if name in simInfo.economyDirectory:
            raise UniqueError("Economy %s already exists" % name)
        else:
            simInfo.economyDirectory[name] = self
        self.banks = []
        self.investments = []
        if params is None:
            params = Parameters()
        self.params = params
        self.simInfo = simInfo

    def add_bank(self, bank):
        self.banks.append(bank)

    def create_investment(self):
        """Create a new investment in this economy

        """
        iName = "%s-inv%r" % (self.name, len(self.investments))
        newI = Investment(self.simInfo, self, iName)
        self.investments.append(newI)
        self.simInfo.assetNetwork.add_node(newI)
        # all investments start out with price 1
        newI.set_price(1.0)
        logger.debug("Created %s" % newI)
        return newI

    def create_investments(self, number):
        """Create a specified number of investments

        @param number:
        """
        for i in range(number):
            self.create_investment()

    def do_investment_shock(self):
        """Apply an investment shock to this economy

        the factor to apply and the proportion of investments to which to apply it are specified in parameters
        @rtype : list
        @return : list of investments that were revalued
        """
        when = self.simInfo.updateCount

        # default is not to apply a shock
        factor = self.params.get('investmentShockFactor', default=1.0)
        # default is to revalue all investments in the economy
        prop = self.params.get('investmentShockProportion', default=1.0)
        if factor > 0.0 and prop > 0:
            logger.info("%r.  %s investment shock: %f on %f of investments" % (when, self, factor, prop))
            return self.revalue_investments(1 - factor, prop)
        else:
            # no effect
            return []

    def revalue_investments(self, factor, proportion=1):
        """Apply a revaluation factor to a proportion of investments in this economy.

        A factor of 1 means no change.

        @rtype : list
        @param factor:
        @return : list of investments that were revalued
        """
        victims = self.get_investments(proportion)
        for inv in victims:
            newPrice = inv.currentPrice * factor
            inv.set_price(newPrice)
        return victims

    def reset(self):
        """Reset the economy at the start of a simulation run

        Create some new investments
        """

        # ditch the existing investments, if any
        self.investments = []
        self.create_investments(self.params.get('investmentCount'))

    def get_investments(self, diversity=0):
        """get a list of investments offering the required level of diversity

        @param diversity:
        """
        ans = get_diverse_sample(self.investments, diversity)
        return ans

    def get_other_investments(self, diversity=0):
        """get a list of investments from other economies offering the required level of diversity

        @param diversity:
        """
        otherInv = []
        for econ in [e for e in self.simInfo.economyDirectory.values() if e != self]:
            otherInv.extend(econ.investments)
        return get_diverse_sample(otherInv, diversity)

    def do_deposit_withdrawals(self, prop):
        """Withdraw a proportion of deposits from all banks in this economy

        @param prop:
        """
        when = self.simInfo.updateCount

        if prop > 1 or prop < 0:
            raise ProportionError("Proportion %r is outside the range [0, 1] when doing deposit withdrawals" % prop)

        logger.info("%r. Doing deposit withdrawals in %s: %f" % (when, self, prop))
        for b in self.banks:
            b.withdraw_deposits(prop)


class Investment(SimulationObject):
    """Represents an investment outside the financial system.

    Every investment has a current price.
    It belongs to an economy.
    Attributes
        name
        currentPrice
        economy
        issued
    """

    def __init__(self, simInfo, economy, name):
        super(Investment, self).__init__(simInfo, name)

        self.currentPrice = 1.0
        self.economy = economy
        self.issued = 0.0
        self.priceHistory = []
        self.holdingHistory = {}

    def buy(self, quantity, buyer):
        """Create a holding of the specified amount

        A holding is an edge in the asset network.
        The amount issued is the total created so far
        @param buyer:
        @param quantity:
        @return: the quantity actually bought and the consideration
        """

        # don't allow negative purchases
        if quantity < 0.0:
            return 0.0, 0.0

        # see if this buyer already has some
        current = network.get_asset_holding(self.simInfo, self, buyer)
        newH = current + quantity
        network.set_asset_holding(self.simInfo, self, buyer, newH)
        self.issued += quantity
        self.record_holding_history(buyer, newH)

        return quantity, quantity * self.currentPrice

    def sell(self, quantity, seller):

        """Sell the specified quantity

        we assume that when we sell, somebody else buys it so the amount issued doesn't change
        @param quantity:
        @param seller:
        @return: the quantity sold and the realised amount
        """

        # see how much this seller has
        current = network.get_asset_holding(self.simInfo, self, seller)
        # scale the quantity if necessary
        quantity = min(quantity, current)
        # don't allow negative sales
        if quantity <= 0.0:
            return 0.0, 0.0

        newH = current - quantity
        # calculate the price
        fireSaleFactor = self.get_param('fireSaleFactor', 0.0)
        if fireSaleFactor > 0.0:
            priceFactor = math.exp(-fireSaleFactor * quantity / self.issued)
            newPrice = self.currentPrice * priceFactor
            self.set_price(newPrice)
        # update the holding
        network.set_asset_holding(self.simInfo, self, seller, newH)
        self.record_holding_history(seller, newH)

        return quantity, quantity * self.currentPrice

    def value(self, holder):
        """the current value of the holding of the specified holder

        @param holder:
        """
        return network.get_asset_holding(self.simInfo, self, holder) * self.currentPrice

    def quantity(self, holder):
        return network.get_asset_holding(self.simInfo, self, holder)

    def holders(self):
        return self.simInfo.assetNetwork.neighbors(self)

    def get_param(self, pName, default=None):
        return self.economy.params.get(pName, default)

    def record_price_history(self, price):
        when = self.simInfo.updateCount
        if self.priceHistory and self.priceHistory[-1][0] == when:   # we've already had one for this update count
            self.priceHistory[-1] = (when, price)
        else:
            self.priceHistory.append((when, price))

    def record_holding_history(self, holder, amount):
        when = self.simInfo.updateCount
        if holder in self.holdingHistory:
            if self.holdingHistory[holder][-1][0] == when:   # we've already had one for this update count
                self.holdingHistory[holder][-1] = (when, amount)
            else:
                self.holdingHistory[holder].append((when, amount))
        else:
            self.holdingHistory[holder] = [(when, amount)]

    def set_price(self, newPrice):
        self.currentPrice = newPrice
        self.record_price_history(newPrice)
