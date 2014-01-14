__author__ = 'Louise'
__version__ = '0.7'

import random
from collections import deque
import logging
from datetime import datetime
from operator import itemgetter

import network
from utils import Parameters, ParameterError, ParameterDefinitions, get_value_from_pList, SimulationInfo
from economy import Economy
from bank import Bank
import results


logger = logging.getLogger("fc")
bankLogger = None


def setup_simulation(pList, bGraph):
    """setup and run a simulation, supplying the parameters as a list and the possible bank lending as a directed graph

    @param pList: A list of parameter tuples.
                    Each tuple consists of the following:
                    entityType      simulator, economy or bank
                    entityName
                    dataType        parameter or attribute
                    dataName
                    dataValue       a string
    @param bGraph: A DiGraph with bank ids as nodes, specifying the possible bank lending
    @return: a 2-tuple (bankHistories, investmentHistories)
                bankHistories is a named 3-tuple of lists
                    balanceSheets: a list of BalanceSheetRecords, which are named 8-tuples:
                                    when bankId lending investments cash borrowing deposits capital
                    borrowings: a list of BorrowingRecords, which are named 4-tuples:
                                    when fromBankId toBankId amount
                    defaults: a list of DefaultRecords, which are named 3-tuples
                                    when bankId ratio
                investmentHistories is a name 2-tuple of lists:
                    holdings: a list of HoldingRecords, which are named 4-tuples
                                    when investmentId bankId amount
                    prices: a list of PriceRecords, which are named 3-tuples
                                    when investmentId price
    @raise:
    """

    simInfo = SimulationInfo()

    simInfo.basicGraph = bGraph  # the graph of possible lending (directed)
    parameterDefs = define_parameters()
    simInfo.tString = datetime.today().strftime("%y%m%d-%H%M")
    simInfo.runDesc = get_value_from_pList(pList, 'simulator', 'simulator', 'parameter', 'runDescriptor')

    if simInfo.runDesc is None:
        msg = "No run descriptor found in parameters"
        logger.error(msg)
        raise ParameterError(msg)

    do_simulator_parameters(simInfo, pList, parameterDefs)

    # note the parameter is an integer, even though any hashable is valid as a seed
    # Strings don't give the same results on different platforms
    seed = simInfo.theParameters.get('randomSeed')
    random.seed(seed)

    do_economy_parameters(simInfo, pList, parameterDefs)
    do_bank_parameters(simInfo, pList, parameterDefs)

    # we've defined all the banks.
    # check that all the banks that have been defined are in basicGraph,
    # and that basicGraph has no extra nodes
    if check_bank_nodes(simInfo):
        # all parameters have now been read in and attached to their objects, so we can now
        # set everything up
        initialise_simulation(simInfo)
    run_simulation(simInfo)

    bankHistories = results.collect_bank_histories(simInfo)
    investmentHistories = results.collect_investment_histories(simInfo)
    logging.shutdown()
    return bankHistories, investmentHistories


def run_simulation(simInfo):
    """Actually run the simulation

    it's all been set up by the time we get here.
    First, apply the shock (if there is one)
    Then update the banks
    do it as many times as necessary
    """
    summarise_whole_state(simInfo)
    do_shocks(simInfo)
    summarise_whole_state(simInfo)
    do_updates(simInfo)
    summarise_whole_state(simInfo)
    summarise_defaults(simInfo)


def initialise_simulation(simInfo):
    """Initialise the simulation at the start of a run

    Need to make sure that all traces of the last run are taken away, but retain the basic structure and
    parameter information
    """

    simInfo.updateCount = 0

    network.reset_networks(simInfo)
    reset_economies(simInfo)
    reset_banks(simInfo)


def do_simulator_parameters(simInfo, pList, parameterDefs):
    """Parse the simulator parameters

    @param pList:
    @param parameterDefs:
    @raise:
    """
    simInfo.theParameters = Parameters(parameterDefs)
    simParams = [(dType, dName, dVal) for eType, eName, dType, dName, dVal in pList if eType == 'simulator']
    if not simParams:
        msg = "No simulator parameters in %s" % simInfo.runDesc
        raise ParameterError(msg)

    simInfo.theParameters.get_params_from_pList(simParams)
    logLevel = simInfo.theParameters.get("logLevel", default="info")
    simInfo.followBank = simInfo.theParameters.get("followBank")
    logDir = simInfo.theParameters.get("logDirectory", default="logs/")
    setup_logging(logLevel, logDir, simInfo)
    logger.info('Setting up run %s' % simInfo.runDesc + simInfo.tString)
    if bankLogger:
        bankLogger.info('Setting up run %s' % simInfo.runDesc + simInfo.tString)
        bankLogger.info('fincat version %s' % __version__)
    logger.info('fincat version %s' % __version__)
    logger.info('Parameters:')
    for eType, eName, dType, dName, dVal in pList:
        if dType == 'parameter':
            logger.info("Parameter for %s %s:  %s = %s" % (eType, eName, dName, dVal))
    logger.info('End of parameters')


def do_economy_parameters(simInfo, pList, parameterDefs):
    """Parse the economy parameters and create the economies

    Each economy must have a name.
    Its parameters inherit from the simulator parameters
    @param pList: list of 5-tuples of parameters
    @param parameterDefs:
    @raise: ParameterError
    """
    economyList = [(eName, dType, dName, dVal) for eType, eName, dType, dName, dVal in pList if eType == 'economy']
    if not economyList:
        msg = "No economy parameters in %s" % simInfo.runDesc
        logging.error(msg)
        raise ParameterError(msg)

    # go through the list, sorted by economy name so all the params for one economy are together
    # and the economies are always created in the same order
    currentName = None
    currentParams = None
    for eName, dType, dName, dVal in sorted(economyList, key=itemgetter(0)):
        if eName != currentName:
            # starting a new one
            currentName = eName
            currentParams = Parameters(parameterDefs, simInfo.theParameters)
            econ = Economy(simInfo, eName, currentParams)
            logger.debug("Setting parameters for %s" % econ)
        if dType == 'parameter':
            currentParams.set(dName, dVal)


def do_bank_parameters(simInfo, pList, parameterDefs):
    """Parse the bank parameters and create the banks

    Each bank must have a name and must belong to an economy.
    Its parameters inherit from those of its economy.
    @param pList: list of 5-tuples of parameters
    @param parameterDefs:
    @raise: ParameterError
    """
    bankList = [(eName, dType, dName, dVal) for eType, eName, dType, dName, dVal in pList if eType == 'bank']
    if not bankList:
        msg = "No bank parameters in %s" % simInfo.runDesc
        logging.error(msg)
        raise ParameterError(msg)

    # go through the list, sorted by bank name so all the params for one bank are together, with attributes
    # before params, and banks are always created in the same order
    currentName = None
    currentParams = None
    currentEconomyName = None
    for eName, dType, dName, dVal in sorted(bankList, key=itemgetter(0, 1)):
        if eName != currentName:
            # starting a new one
            currentName = eName
            currentParams = Parameters(parameterDefs, simInfo.theParameters)
            currentEconomyName = None
            logger.debug("Setting parameters for bank %s" % currentName)

        if dType == 'attribute' and dName == 'economy':
            currentEconomyName = dVal
            if not currentEconomyName in simInfo.economyDirectory:
                msg = "Invalid economy %r specified for bank %s in %s" % (
                    currentEconomyName, currentName, simInfo.runDesc)
                logger.error(msg)
                raise ParameterError(msg)
            econ = simInfo.economyDirectory[currentEconomyName]
            currentParams = Parameters(parameterDefs, econ.params)
            followMe = simInfo.followBank == currentName
            bank = Bank(simInfo, currentName, econ, currentParams, followMe)
            logger.debug("Created %s" % bank)

        elif dType == 'parameter':
            if not currentEconomyName:
                msg = "No economy specified for bank %s in %s" % (currentName, simInfo.runDesc)
                logger.error(msg)
                raise ParameterError(msg)
            currentParams.set(dName, dVal)


def reset_economies(simInfo):
    """Reset the economies at the start of a run

    @return:
    """
    for econ in simInfo.economyDirectory.values():
        econ.reset()


def reset_banks(simInfo):
    """Reset the bank information at the start of a run

    First, set up the bank lending.
    From that, we can calculate the other elements of the balance sheet
    """
    for bank in simInfo.get_banks():
        bank.reset()

    initialise_bank_lending(simInfo)
    # we've now set up the bank lending, which dictates the financial position of each bank, which we can now calculate
    initialise_balance_sheets(simInfo)


def check_bank_nodes(simInfo):
    """Are the banks in the basic graph the same as the ones in the parameter file?

    @return:
    @raise: ParameterError
    """
    graphNodes = frozenset(simInfo.basicGraph.nodes())
    bankIds = frozenset(simInfo.bankDirectory.keys())
    if graphNodes == bankIds:
        return True
    else:
        # find the differences
        notBanks = graphNodes.difference(bankIds)
        notInGraph = bankIds.difference(graphNodes)
        msg = ""
        if notBanks:
            msg += "There are %r nodes in the graph that don't correspond to banks" % len(notBanks)
        if notInGraph:
            msg += "\nThere are %r banks that don't have nodes in the graph" % len(notInGraph)
        msg += "\nLook at: "
        for e in notBanks.union(notInGraph):
            msg += " %s" % e
        logger.error(msg)
        raise ParameterError(msg)


def initialise_bank_lending(simInfo):
    """Initialise the bank lending at the start of a run

    Check that the banks in the graph of possible lending are the same as those in the parameter file.
    If they are, create interbank loans. Use the bankSize and bankSD parameters of the lending bank
    to get a normal rv for the size of the loan
    @raise: ParameterError
    """

    # first sort the edges so we always do them in the same order
    eList = sorted(simInfo.basicGraph.edges())
    for u, v in eList:
        if u == v:
            raise ParameterError("Bank can't lend to itself: %s" % u)
        bFrom = simInfo.bankDirectory[u]
        bTo = simInfo.bankDirectory[v]
        mu = bFrom.get_param('loanSize', required=True)
        loanSizeType = bFrom.get_param('loanSizeType', default='perLoan')
        if loanSizeType == 'perBank':
            counterpartyCount = simInfo.basicGraph.out_degree(u)
            mu = mu / counterpartyCount  # split the total loans among all counterparties
        sigma = bFrom.get_param('loanSD', required=True)
        amount = max(0, random.normalvariate(mu, sigma))
        bFrom.add_loan(bTo, amount)


def initialise_balance_sheets(simInfo):
    """Set up the balance sheets of the banks


    """
    iMethod = get_param(simInfo, 'balanceSheetMethod', default='capitalRatio')
    for b in simInfo.get_banks():
        b.initialise_balance_sheet(iMethod)


def setup_logging(logLevel, logDir, simInfo):
    """Set up the logging for the simulation

    @param logLevel:
    @param logDir:
    """
    global logger, bankLogger

    # Configure logging parameters so we get output while the program runs
    if logLevel == "info":
        logger.setLevel(logging.INFO)
    elif logLevel == "debug":
        logger.setLevel(logging.DEBUG)
    if not logger.handlers:
        logFile = logDir + simInfo.runDesc + '-' + simInfo.tString + ".log"
        fh = logging.FileHandler(logFile, mode='w')
        ft = logging.Formatter(fmt='%(asctime)s %(name)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        fh.setFormatter(ft)
        logger.addHandler(fh)
        logger.propagate = False  # stop it going to stdout

    if simInfo.followBank:  # if there is a bank for which we want detailed info, set up a logger
        fBank = simInfo.followBank.replace(' ', '')
        fBank = fBank.replace("'", "")
        fBank = fBank.replace("-", "")
        bankLogger = logging.getLogger("fc." + simInfo.followBank)
        bankLogger.setLevel(logging.DEBUG)
        if not bankLogger.handlers:
            logFile = logDir + fBank + '-' + simInfo.tString + ".log"
            fh = logging.FileHandler(logFile, mode='w')
            ft = logging.Formatter(fmt='%(asctime)s %(name)s %(message)s  <%(funcName)s>', datefmt='%Y-%m-%d %H:%M:%S')
            fh.setFormatter(ft)
            bankLogger.addHandler(fh)
            bankLogger.propagate = False


def define_parameters():
    """Define the valid parameters for the simulation

    Parameter                applied    description
    runDescriptor            simulator  string used to identify log an output files
    logDirectory             simulator  directory for log and output files
    logLevel                 simulator  logging level (debug, info, warning, error)
    graphFile                simulator  the basic lending graph
    randomSeed               simulator  seed for random number generator
    followBank               simulator  the bank (if any) to do detailed logging on
    runCount                 simulator  number of simulations to perform
    outputFreq               simulator  how often to write output files (every x updates)
    balanceSheetMethod       simulator  how to initialise the balance sheet (ear or cr)
    fireSaleFactor           economy    decreases investment prices on sale
    investmentCount          economy    number of investments in economy at outset
    investmentShockFactor    economy    change in investment values as a shock event at the outset
    investmentShockProportion economy   proportion of investments in the economy that the shock is applied to
    targetCashProportion     bank       desired prop of assets to hold in cash
    assetSalesFactor         bank       fudge factor when selling investments
    maxDefaultRatio          bank       maximum proportion when defaulting on liabilities
    loanSize                 bank       mean amount of bank lending at outset
    loanSD                   bank       sd of bank lending at outset
    loanSizeType             bank       whether loanSize refers to individual loans, or total for the bank
    externalAssetRatio       bank       initial ratio of investments and cash to capital (not used)
    capitalRatio             bank       initial ratio of capital to total assets
    cashRatio                bank       initial ratio of cash to total assets
    financialLiabilityRatio  bank       initial ratio of bank borrowing to total liabilities
    financialAssetRatio      bank       initial ratio of bank lending to total assets
    homeInvestmentProp       bank       initial proportion of investments in home economy
    homeInvestmentDiversity  bank       diversity of investments among those available in home economy
    awayInvestmentDiversity  bank       diversity of investments among those available other than in home economy
    liquidateOnDefault       bank       going bust means the bank sells all its investments
    defaultWhenIlliquid      bank       running out of cash means the bank goes bust
    depositShockFactor       bank       proportion of deposits withdrawn as a shock event at the outset
    loanShockFactor          bank       proportion of bank's borrowing that matures as a shock event at the outset

    Note that it may not make sense to define a parameter at the level at which it's applied. For example,
    defaultWhenIlliquid should probably be the same for all banks
    @return:
    """
    parameterDefs = ParameterDefinitions()

    parameterDefs.add_definition('runDescriptor', str)
    parameterDefs.add_definition('logDirectory', str)
    parameterDefs.add_definition('logLevel', str,
                                 pValid=['INFO', 'DEBUG', 'ERROR', 'WARNING', 'info', 'debug', 'error', 'warning'])
    parameterDefs.add_definition('graphFile', str)
    parameterDefs.add_definition('randomSeed', int)  # can be any hashable object, but need int for x-platform consistency
    parameterDefs.add_definition('followBank', str)
    parameterDefs.add_definition('balanceSheetMethod', str, pValid=["assets", "liabilities", "None"])
    parameterDefs.add_definition('fireSaleFactor', float, pValid=[0, 9999])
    parameterDefs.add_definition('investmentCount', int, pValid=[0, 9999])
    parameterDefs.add_definition('investmentShockFactor', float, pValid=[0, 1])
    parameterDefs.add_definition('investmentShockProportion', float, pValid=[0, 1])
    parameterDefs.add_definition('targetCashProportion', float, pValid=[0, 1])
    parameterDefs.add_definition('assetSalesFactor', float, pValid=[1, 10])
    parameterDefs.add_definition('maxDefaultRatio', float, pValid=[0.0, 1.0])
    parameterDefs.add_definition('loanSize', int)
    parameterDefs.add_definition('loanSizeType', str, pValid=['perLoan', 'perBank'])
    parameterDefs.add_definition('loanSD', float)
    parameterDefs.add_definition('externalAssetRatio', float, pValid=[0, 1000])
    parameterDefs.add_definition('cashRatio', float, pValid=[0.00001, 1])
    parameterDefs.add_definition('capitalRatio', float, pValid=[0.00001, 0.9999])
    parameterDefs.add_definition('financialLiabilityRatio', float, pValid=[0.00001, 1])
    parameterDefs.add_definition('financialAssetRatio', float, pValid=[0.00001, 1])
    parameterDefs.add_definition('homeInvestmentProp', float, pValid=[0, 1])
    parameterDefs.add_definition('homeInvestmentDiversity', float, pValid=[0, 1])
    parameterDefs.add_definition('awayInvestmentDiversity', float, pValid=[0, 1])
    parameterDefs.add_definition('depositShockFactor', float, pValid=[0, 1])
    parameterDefs.add_definition('loanShockFactor', float, pValid=[0, 1])

    # TODO: implement the following parameters
    parameterDefs.add_definition('runCount', int, [0, 99999])
    parameterDefs.add_definition('outputFreq', int, [0, 99999])
    parameterDefs.add_definition('defaultWhenIlliquid', 'bool')
    parameterDefs.add_definition('liquidateOnDefault', 'bool')
    parameterDefs.add_definition('queueMechanism', str, pValid=['LIFO', 'FIFO', 'Random', 'RANDOM', 'Fixed', 'FIXED'])

    return parameterDefs


def do_shocks(simInfo):
    """Apply the shocks at the outset of the simulation

    The investment shocks are applied to the economies first,
    then the deposit withdrawals and loan maturities to the banks
    """
    simInfo.updateCount += 1
    logger.info("%r. Doing initial shocks" % simInfo.updateCount)
    for econ in simInfo.economyDirectory.values():
        econ.do_investment_shock()
        # needn't shuffle the banks as the order in which this is done doesn't affect anything
    for bank in simInfo.get_banks():
        bank.do_deposit_shock()
        bank.do_loan_shock()
        bank.record_state()


def do_updates(simInfo):
    """Update the banks until the situation settles down

    Go through the banks, updating each one, and adding those that are affected by this bank to the list.
    Continue doing this until the effects die out.
    """
    # get all the banks, making sure we start off with them in the same order
    allBanks = simInfo.get_banks()
    random.shuffle(allBanks)
    banksToDo = deque(allBanks)

    while banksToDo:
        simInfo.updateCount += 1
        # while there's something there
        theBank = banksToDo.popleft()
        logger.info("%r. Updating %s" % (simInfo.updateCount, theBank))
        affected, prop = theBank.update()

        if affected:
            logger.info("%r.    %r banks affected" % (simInfo.updateCount, len(affected)))
        else:
            logger.info("%r.    No banks affected" % simInfo.updateCount)
        for other in affected:
            if not other in banksToDo:
                logger.info("%r.      %s added to the list" % (simInfo.updateCount, other))
                banksToDo.append(other)
            else:
                logger.info("%r.      %s already in the list" % (simInfo.updateCount, other))
            if other.followMe:
                other.logger.debug("%r. Affected by update to %s" % (simInfo.updateCount, theBank))


def get_param(simInfo, pName, default=None):
    """Get the value of a simulation parameter

    @param pName: name of the parameter whose value we want
    @param default: default value to use if the parameter hasn't been set
    @return:
    """
    if simInfo.theParameters:
        return simInfo.theParameters.get(pName, default)
    else:
        return default


def summarise_defaults(simInfo):
    defaulted = [bank for bank in simInfo.get_banks() if bank.totalDefault < 1.0]
    logger.info("%r                        The following %r banks defaulted:\n" % (simInfo.updateCount, len(defaulted)))
    for bank in defaulted:
        logger.info("%r              %s  default ratio: %f" % (simInfo.updateCount, bank, bank.totalDefault))


def summarise_whole_state(simInfo):
    logger.info("%r. \n\n                        Current state:\n" % simInfo.updateCount)
    insolvent = []
    justSolvent = []
    for bank in simInfo.get_banks():
        maxDefaultRatio = bank.get_param('maxDefaultRatio', default=1.0)
        capRatio = bank.total_assets() / bank.total_liabilities()
        if capRatio < maxDefaultRatio:
            insolvent.append(bank)
        elif 1 / capRatio > maxDefaultRatio:
            justSolvent.append(bank)
    logger.info("%r.    There are %r insolvent banks" % (simInfo.updateCount, len(insolvent)))
    for bank in insolvent:
        logger.info("%r.         %s has capital %f (%6.4f%%)" % (simInfo.updateCount, bank, bank.equity_value(),
                                                            bank.capital_ratio()*100))
    logger.info("%r.\n\n" % simInfo.updateCount)
    logger.info("%r.    There are %r barely solvent banks" % (simInfo.updateCount, len(justSolvent)))
    for bank in justSolvent:
        logger.info("%r.         %s has capital %f (%6.4f%%)" % (simInfo.updateCount, bank, bank.equity_value(),
                                                            bank.capital_ratio()*100))
    logger.info("%r.\n\n" % simInfo.updateCount)
