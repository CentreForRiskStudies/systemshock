__author__ = 'Louise'

import logging

import network
from utils import ProportionError, UniqueError, ParameterError, BalanceSheetRecord, SimulationObject


logger = logging.getLogger("fc." + __name__)


class Bank(SimulationObject):

    def __init__(self, simInfo, name, econ, params, followMe=False):
        """
        A bank has assets and liabilities
        Its assets consist of loans to other banks,  external investments and cash
        Its liabilities consist of loans from other banks, and loans (deposits) from outside the financial system
        The excess of its assets over its liabilities constitutes its equity

        @param name:
        """
        super(Bank, self).__init__(simInfo, name)

        if name in simInfo.bankDirectory:
            raise UniqueError("Bank %s already exists" % name)
        else:
            simInfo.bankDirectory[name] = self
        self.economy = econ
        self.parameters = params
        econ.add_bank(self)

        # make sure it appears in the networks, even if it's not connected to anything
        simInfo.assetNetwork.add_node(self)
        simInfo.loanNetwork.add_node(self)
        if followMe:
            self.followMe = True
            self.logger = logging.getLogger("fc." + self.name)
            self.logger.debug("\n\nCreating bank %s", self)
        else:
            self.followMe = False
            # set everything to zero
        self.reset()

    def reset(self):
        self.cash = 0
        self.deposits = 0
        self.solvent = True
        self.liquid = True
        self.defaultHistory = []
        self.borrowingHistory = {}
        self.stateHistory = []
        self.totalDefault = 1.0

    def investment_value(self):
        return network.get_portfolio_value(self.simInfo, self)

    def total_lending(self):
        return network.bank_lending(self.simInfo, self)

    def total_assets(self):
        lending = self.total_lending()
        inv = self.investment_value()
        return lending + inv + self.cash

    def total_borrowing(self):
        return network.bank_borrowing(self.simInfo, self)

    def total_liabilities(self):
        return self.total_borrowing() + self.deposits

    def equity_value(self):
        """The bank's equity: excess of assets over liabilities

        @return:
        """
        return self.total_assets() - self.total_liabilities()

    def external_asset_ratio(self):
        """the ratio of external assets to the bank's equity

        @return:
        """
        return (self.investment_value() + self.cash) / self.equity_value()

    def financial_liability_ratio(self):
        """The ratio of within-network liabilities to all liabilities

        @return:
        """
        return self.total_borrowing() / self.total_liabilities()

    def financial_asset_ratio(self):
        """the ratio of within-network assets to all assets


        @return:
        """
        return self.total_lending() / self.total_assets()

    def capital_ratio(self):
        if self.total_assets() == 0:
            return 0
        else:
            return self.equity_value() / self.total_assets()

    def withdraw_deposits(self, prop):
        """Deposits are withdrawn from this bank, so it pays out cash

        @param prop:
        """
        when = self.simInfo.updateCount
        if prop > 1 or prop < 0:
            raise ProportionError("Proportion %r is outside the range [0, 1] when withdrawing deposits" % prop)

        logger.info("%r. Withdrawing %f of deposits from %s" % (when, prop, self))
        withdrawn = prop * self.deposits
        self.cash -= withdrawn
        self.deposits -= withdrawn
        if self.followMe:
            self.logger.debug("%r.  Withdrawing %f of deposits: %f" % (when, prop, withdrawn))
            self.logger.debug("%r.    New deposits: %f, new cash: %f" % (when, self.deposits, self.cash))

    def liquidise(self, targetProp, fudgeFactor):
        """Adjust the assets so that there is no negative cash.

        (liquidise as in make something liquid)
        Sell off investments to bring cash up to the desired proportion.
        Don't do anything if the cash proportion is too high.
        Can't do anything if you've run out of investments to sell
        @param targetProp: proportion of asset that should be cash
        @param fudgeFactor: make sure things converge
        """
        when = self.simInfo.updateCount

        currentAssets = self.total_assets()
        currentInvestments = self.investment_value()
        if self.followMe:
            self.logger.debug("%r. Liquidising..." % when)
            self.logger.debug("%r.   Total assets: %f  of which investments: %f, cash: %f" %
                              (when, currentAssets, currentInvestments, self.cash))
        if self.cash < 0.0:
            # current cash is negative and counted within total assets which isn't what we want
            currentAssets -= self.cash
        targetCash = targetProp * currentAssets  # this is what we're aiming for
        if self.followMe:
            self.logger.debug("%r.  Target cash: %f" % (when, targetCash))
        if self.cash >= targetCash or currentInvestments <= 0:
            return []  # nothing to do
            # because of the effect of the sale of investments, we won't realise as much as we think we will
        # so we apply a fudge factor that, hopefully, will make us overshoot a little or, at least,
        # do fewer iterations than we otherwise would.
        logger.info("%r.      %s selling investments..." % (when, self))
        affected = self.get_sharing_banks()
        while targetCash > self.cash and currentInvestments > 0:
            targetSales = fudgeFactor * (targetCash - self.cash)
            # we reduce all the investment holdings by the same proportion
            prop = min(1.0, targetSales / currentInvestments)
            if self.followMe:
                self.logger.debug("%r.  Target sales : %f" % (when, targetSales))
            self.reduce_investments(prop)
            currentInvestments = self.investment_value()
            if self.followMe:
                self.logger.debug("%r.  Investments are now: %f, cash %f" % (when, currentInvestments, self.cash))
        if self.followMe:
            for bank, inv, eData in self.simInfo.assetNetwork.edges(self, data=True):
                self.logger.debug("  %s: price %f, quantity %f, value of holding %f" % (inv, inv.currentPrice,
                                                                                        inv.quantity(bank),
                                                                                        inv.value(bank)))

        return affected

    def reduce_investments(self, prop):
        """Reduce all this bank's investment holdings by the given proportion

        @param prop:
        """
        when = self.simInfo.updateCount
        total = 0

        if prop > 1 or prop < 0:
            raise ProportionError("Proportion %r is outside the range [0, 1] when reducing investments" % prop)

        if self.followMe:
            self.logger.debug("%r.    Reducing investments by %f" % (when, prop))
        for inv in self.get_investments():
            qToSell = prop * inv.quantity(self)
            qSold, realised = inv.sell(qToSell, self)
            self.cash += realised
            total += realised
            if self.followMe:
                self.logger.debug("%r.      Realised %f from %s; cash now %f" % (when, realised, inv, self.cash))
        if self.followMe:
            self.logger.debug("%r.    Realised %f in total" % (when, total))

    def get_investments(self):
        return self.simInfo.assetNetwork.neighbors(self)

    def get_sharing_banks(self):
        """Get all banks with an investment in common with the specified bank

        @return:
        """
        ans = set()
        for inv in self.get_investments():
            ans = ans.union(inv.holders())
        if ans:
            ans.remove(self)
        return list(ans)

    def update(self):
        """Update the bank's balance sheet

        Adjust the assets so that there's enough cash
        Check for solvency and liquidity
        """
        when = self.simInfo.updateCount

        if self.followMe:
            self.logger.debug("%r. Updating..." % when)
        self.check_solvency()
        affected = []
        if self.solvent:
            # liquidising can't improve solvency, so no point if already insolvent
            targetProp = self.parameters.get('targetCashProportion', 0.0)
            fudgeFactor = self.parameters.get('assetSalesFactor', 1.0)
            affected = self.liquidise(targetProp, fudgeFactor)
            # this could send it bust...
            self.check_solvency()
            self.check_liquidity()

        # TODO what to do if it's not liquid??
        if not self.solvent:
            dAffected, ratio = self.default_on_liabilities()
            affected += dAffected
        else:
            ratio = None

        self.record_state()
        return affected, ratio

    def default_on_liabilities(self):
        """Deal with a bank that is insolvent

        All the bank's liabilities are written down pro-rata.
        """
        when = self.simInfo.updateCount

        currentAssets = self.total_assets()
        currentLiabilities = self.total_liabilities()
        if self.followMe:
            self.logger.debug("%r. Defaulting..." % when)
            self.logger.debug("%r.  Total assets: %f  of which cash: %f, total liabilities: %f" %
                              (when, currentAssets, self.cash, currentLiabilities))
        if currentLiabilities == 0:
            if self.followMe:
                self.logger("%r.  ... but has zero liabilities" % when)
            self.record_default(0.0)
            return [], 0.0
        ratio = max(0, currentAssets / currentLiabilities)
        if ratio > 1:
            msg = ("%r. %s has defaulted but its assets (%f) are more than its liabilities (%f)" %
                   (when, self, currentAssets, currentLiabilities))
            if self.followMe:
                self.logger.error(msg)
            raise ProportionError(msg)
        maxRatio = self.get_param('maxDefaultRatio', default=1.0)
        ratio = min(maxRatio, ratio)
        logger.info("%r.     %s capital: %r" % (when, self, self.equity_value()))
        logger.info("%r.     %s default proportion: %r" % (when, self, ratio))

        self.record_default(ratio)
        self.deposits *= ratio
        lenders = network.do_default_loans(self.simInfo, self, ratio)
        return lenders, ratio

    def do_deposit_shock(self):
        """Apply the deposit shock to this bank


        """
        # default is no withdrawals
        shockFactor = self.get_param('depositShockFactor', default=0.0)
        if shockFactor > 0:
            self.withdraw_deposits(shockFactor)

    def do_loan_shock(self):
        """Apply the loan shock to this bank
        """
        #default is no maturities
        shockFactor = self.get_param('loanShockFactor', default=0.0)
        if shockFactor > 0:
            return network.do_loan_maturities(self.simInfo, self, shockFactor)
        else:
            return []

    def check_solvency(self):
        self.solvent = self.equity_value() >= 0.0
        if self.followMe:
            self.logger.debug("      Check solvency: %r  %f" % (self.solvent, self.equity_value()))

    def check_liquidity(self):
        self.liquid = self.cash >= 0.0
        if self.followMe:
            self.logger.debug("      Check liquidity: %r  %f" % (self.liquid, self.cash))

    def initialise_balance_sheet(self, iMethod):
        """Initialise the balance sheet, based on the bank lending and the parameters

        Two approaches to determining the size of the balance sheet: through the assets and through the liabilities.
        In both cases bank borrowing and lending are predetermined, and we have the desired capital ratio and cash ratio.
        Then we either specify the external asset ratio or the financial liability ratio.
        Finally, we do some adjustments to make sure that nothing is negative.
        """
        capitalRatio = self.get_param('capitalRatio', required=True)
        cashRatio = self.get_param('cashRatio', required=True)
        loans = network.bank_lending(self.simInfo, self)
        borrowings = network.bank_borrowing(self.simInfo, self)

        if iMethod == "assets":
            financialAssetRatio = self.get_param('financialAssetRatio', required=True)
            externalAssets = loans * (1 - financialAssetRatio) / financialAssetRatio
            totalAssets = loans + externalAssets
            self.cash = cashRatio * totalAssets
            initialInvestments = externalAssets - self.cash
            initialCapital = capitalRatio * totalAssets
            self.deposits = totalAssets - borrowings - initialCapital
            if self.deposits < 0:
                # can't have negative deposits. Make them zero, and increase cash by the same amount.
                self.cash -= self.deposits
                self.deposits = 0
                # this will change all the ratios.
        elif iMethod == "liabilities":
            financialLiabilityRatio = self.get_param('financialLiabilityRatio', required=True)
            self.deposits = borrowings / financialLiabilityRatio - borrowings
            initialCapital = (self.deposits + borrowings) * capitalRatio / (1 - capitalRatio)
            self.cash = cashRatio * (self.deposits + borrowings + initialCapital)
            initialInvestments = initialCapital + borrowings + self.deposits - loans - self.cash
            if initialInvestments < 0:
                # can't have negative investments. Make them zero, and increase deposits by the same amount
                self.deposits -= initialInvestments
                initialInvestments = 0
        else:
            msg = "balanceSheetMethod %r not recognised" % iMethod
            logger.error(msg)
            raise ParameterError(msg)

        self.initialise_investments(initialInvestments)
        self.record_state()

    def initialise_investments(self, quantity):
        """give the bank an investment portfolio amounting to the required quantity


        @param: quantity
        """

        # proportion of investments in the home economy
        homeInvestmentProp = self.get_param('homeInvestmentProp', default=1.0)
        homeInvestmentDiversity = self.get_param('homeInvestmentDiversity', default=1.0)
        awayInvestmentDiversity = self.get_param('awayInvestmentDiversity', default=1.0)
        homeInvestments = self.economy.get_investments(homeInvestmentDiversity)
        homeAmount = quantity * homeInvestmentProp / len(homeInvestments)
        for inv in homeInvestments:
            inv.buy(homeAmount, self)
        awayInvestments = self.economy.get_other_investments(awayInvestmentDiversity)
        awayAmount = quantity * (1 - homeInvestmentProp) / len(awayInvestments)
        for inv in awayInvestments:
            inv.buy(awayAmount, self)

    def add_loan(self, tBank, amount):
        """Add a loan from this bank to another one

        @param tBank:
        @param amount:
        """
        self.simInfo.loanNetwork.add_edge(self, tBank, amount=amount)
        tBank.record_borrowing_history(self, amount)
        logger.debug("%r.  Added loan of %f from %s to %s" % (self.simInfo.updateCount, amount, self, tBank))
        if self.followMe:
            self.logger.debug("%r.  Added loan of %f from %s to %s" % (self.simInfo.updateCount, amount, self, tBank))
        if tBank.followMe:
            tBank.logger.debug("%r.  Added loan of %f from %s to %s" % (self.simInfo.updateCount, amount, self, tBank))

    def get_param(self, pName, default=None, required=False):
        pVal = self.parameters.get(pName, default)
        if required and pVal is None:
            raise ParameterError("Parameter %r is not specified for bank %s" % (pName, self))
        else:
            return pVal

    def record_state(self):
        when = self.simInfo.updateCount

        if self.stateHistory:
            lastState = self.stateHistory[-1]
        else:
            lastState = None
        state = BalanceSheetRecord(when, self.name, self.total_lending(), self.investment_value(), self.cash,
                                   self.total_borrowing(), self.deposits, self.equity_value())
        if (not lastState) or state[1:] != lastState[1:]:   # ignore the first element, which is the update count
            self.stateHistory.append(state)
        logger.debug("%r.   %s: %6.4f%% state: %r" % (when, self, self.capital_ratio()*100, state))
        if self.followMe:
            self.logger.debug("%r.   %s: %6.4f%% state: %r" % (when, self, self.capital_ratio()*100, state))

    def record_borrowing_history(self, bFrom, amount):
        """Update the loan history for this loan

        Keep track of the borrowings from other banks
        The history is indexed by bank, and each entry is a list of (when, amount) pairs.
        @param bFrom:
        @param amount:
        """
        when = self.simInfo.updateCount

        if bFrom in self.borrowingHistory:
            lastAmount = self.borrowingHistory[bFrom][-1]
            if amount != lastAmount:
                self.borrowingHistory[bFrom].append((when, amount))
        else:
            self.borrowingHistory[bFrom] = [(when, amount)]
        if self.followMe:
            self.logger.debug("%r.   loan from %s to %s is now %r" %(when, bFrom, self, amount))
        if bFrom.followMe:
            bFrom.logger.debug("%r.   loan from %s to %s is now %r" % (when, self, bFrom, amount))

    def record_default(self, ratio):
        when = self.simInfo.updateCount

        self.defaultHistory.append((when, ratio))
        self.totalDefault *= ratio

    def has_defaulted(self):
        return self.totalDefault < 1.0
