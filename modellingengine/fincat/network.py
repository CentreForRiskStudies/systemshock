__author__ = 'Louise'

import logging

import networkx as nx

from utils import ProportionError

logger = logging.getLogger("fc." + __name__)


def clear_networks(simInfo):
    """Initialise the graphs to empty graphs

    Used for testing, and maybe elsewhere too.
    """
    simInfo.loanNetwork = nx.DiGraph()
    simInfo.assetNetwork = nx.Graph()


def reset_networks(simInfo):
    """reset the networks at the start of a simulation run

    Need to keep only the bank nodes. The investments are re-created as part of the run.
    """
    oldLoanNetwork = simInfo.loanNetwork
    clear_networks(simInfo)
    # add the banks back in as nodes
    simInfo.loanNetwork.add_nodes_from(oldLoanNetwork.nodes())
    simInfo.assetNetwork.add_nodes_from(oldLoanNetwork.nodes())


def do_loan_changes(simInfo, bank, prop, isDefault):
    """Make changes to the specified bank's borrowings.

    There are two possibilities: the bank is defaulting on its borrowings, or redeeming some of them
    (the loans are maturing).

    If it's a default, the bank defaults on (1 - prop) of its outstanding borrowings (ie, after defaulting,
    the outstanding borrowings are the original outstanding amount multiplied by prop).

    If it's a loan maturity, the specified proportion of loans are redeemed for cash.

    @param simInfo:
    @param bank: the bank whose borrowings are changed
    @param prop: the proportion applied.
    @param isDefault: true if this is a default, false if it's loan maturities
    @return: @raise:
    """
    if isDefault:
        opString = "defaults"
    else:
        opString = "maturities"
    if prop > 1 or prop < 0:
        raise ProportionError("Proportion %r is outside the range [0, 1] when doing loan %s" % (prop, opString))
    if bank.followMe:
        bank.logger.debug("%r. Doing loan %s (%f)" % (simInfo.updateCount, opString, prop))
    lenders = simInfo.loanNetwork.predecessors(bank)
    for counterparty in lenders:
        amt = simInfo.loanNetwork[counterparty][bank]['amount']
        if isDefault:
            newAmount = amt * prop
        else:
            proceeds = prop * amt
            counterparty.cash += proceeds
            bank.cash -= proceeds
            newAmount = amt - proceeds

        if newAmount == 0.0:
            simInfo.loanNetwork.remove_edge(counterparty, bank)
        else:
            simInfo.loanNetwork[counterparty][bank]['amount'] = newAmount
        bank.record_borrowing_history(counterparty, newAmount)
    return lenders


def do_loan_maturities(simInfo, bank, prop):
    """Handle loan maturities, pushing the cash flows to the banks.

    Each bank has a parameter that specifies the proportion of its borrowing that matures
    """
    when = simInfo.updateCount
    logger.info("%r. Doing loan maturities for %s " % (when, bank))

    return do_loan_changes(simInfo, bank, prop, False)


def do_default_loans(simInfo, bank, prop):
    """Default loans to bank, as it's insolvent

    The loans are written down to the specified proportion.
    The banks that are affected are those that have lent to this bank
    @param bank:
    @param prop:
    @return:
    @raise:
    """
    return do_loan_changes(simInfo, bank, prop, True)


def bank_lending(simInfo, bank, other=None):
    """Get the bank lending from the specified bank to another bank or in total

    if the other bank is None, get the total lending from the specified bank
    @param bank:
    @param other:
    """
    # out edges from the bank
    if other is None:
        ans = simInfo.loanNetwork.out_degree(bank, weight='amount')
        if bank.followMe:
            bank.logger.debug("       Total lending is: %f" % ans)
    elif other in simInfo.loanNetwork.successors(bank):
        ans = simInfo.loanNetwork[bank][other]['amount']
        if bank.followMe:
            bank.logger.debug("       Lending to %s is: %f" % (other, ans))
    else:
        ans = 0
        if bank.followMe:
            bank.logger.debug("       No lending to %s" % other)
    return ans


def bank_borrowing(simInfo, bank, other=None):
    """get the bank borrowing to the specified bank from another bank or in total

    @param bank:
    @return:
    """
    if other is None:
        ans = simInfo.loanNetwork.in_degree(bank, weight='amount')
        if bank.followMe:
            bank.logger.debug("       Total borrowing is: %f" % ans)
    elif other in simInfo.loanNetwork.predecessors(bank):
        ans = simInfo.loanNetwork[other][bank]['amount']
        if bank.followMe:
            bank.logger.debug("       Borrowing from %s is: %f" % (other, ans))
    else:
        ans = 0
        if bank.followMe:
            bank.logger.debug("       No borrowing from %s" % other)
    return ans


def get_asset_holding(simInfo, investment, bank):
    """Get the quantity of an investment held by a bank

    @param investment:
    @param bank:
    @return:
    """
    if simInfo.assetNetwork.has_edge(investment, bank):
        return float(simInfo.assetNetwork.get_edge_data(investment, bank)['amount'])
    else:
        return 0.0


def set_asset_holding(simInfo, investment, bank, quantity):
    """Set the quantity of an investment held by a bank

    if the quantity is zero, remove the edge if it exists
    @param investment:
    @param bank:
    @param quantity:
    """
    if quantity > 0.0:
        # updates if the edge already exists
        simInfo.assetNetwork.add_edge(investment, bank, amount=quantity)
    elif simInfo.assetNetwork.has_edge(investment, bank):
        simInfo.assetNetwork.remove_edge(investment, bank)


def get_asset_volume(simInfo, investment):
    return simInfo.assetNetwork.degree(investment, weight='amount')


def get_portfolio_value(simInfo, bank):
    # this relies on G.edges(node) always returning edges as (node, other) tuples.
    return sum([inv.currentPrice * float(eData['amount']) for bank, inv, eData in simInfo.assetNetwork.edges(bank, data=True)])
