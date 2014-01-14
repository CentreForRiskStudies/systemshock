__author__ = 'Louise'

from bank import Bank
from economy import Economy
from utils import PriceRecord, HoldingRecord, InvestmentHistory, BankHistory, BorrowingRecord, DefaultRecord


def collect_bank_histories(simInfo, bankList=None):
    """collect a list of tuples giving the history of the bank balance sheets

    Produce a list of tuples giving the balance sheets of banks. Each tuple is:
    (updateCount, bankName, totalLending, investmentValue, cash, totalBorrowing, deposits, equityValue
    @param bankList: a bank or economy or list of banks specifying the banks. If None, do all banks
    @return:
    """
    bankList = _make_bank_list(simInfo, bankList)
    bSheetList = []
    bHistories = []
    dHistories = []

    for thisBank in bankList:
        bSheetList += thisBank.stateHistory
        for fromBank, bHistory in thisBank.borrowingHistory.items():
            for when, amount in bHistory:
                bHistories.append(BorrowingRecord(when, fromBank.name, thisBank.name, amount))
        for when, ratio in thisBank.defaultHistory:
            dHistories.append(DefaultRecord(when, thisBank.name, ratio))

    return BankHistory(sorted(bSheetList), sorted(bHistories),
                       sorted(dHistories))  # this will sort on 1st element of the tuple


def collect_investment_histories(simInfo):
    hHistories = []
    pHistories = []
    for economy in simInfo.economyDirectory.values():
        for investment in economy.investments:
            for bank, hList in investment.holdingHistory.items():
                for hTuple in hList:
                    hHistories.append(HoldingRecord(hTuple[0], investment.name, bank.name, hTuple[1]))
            for when, price in investment.priceHistory:
                pHistories.append(PriceRecord(when, investment.name, price))
    return InvestmentHistory(sorted(hHistories), sorted(pHistories))


def _make_bank_list(simInfo, starter):
    """Make a list of banks from a motley collection of banks and economies

    @param starter:
    @return:
    """
    if starter is None:
        bankList = simInfo.bankDirectory.values()
    elif isinstance(starter, Bank):
        bankList = [starter]
    elif isinstance(starter, Economy):
        bankList = starter.banks[:]   # take a copy
    else:
        bankList = []
        for elt in starter:  # we'll be in trouble if it's not iterable...
            if isinstance(elt, Bank):
                bankList.append(elt)
            elif isinstance(elt, Economy):
                bankList += starter.banks
    return bankList
