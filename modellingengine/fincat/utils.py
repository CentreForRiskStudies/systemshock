__author__ = 'Louise'

import xml.etree.ElementTree as ET
import random
import math
import logging
import networkx as nx
from collections import namedtuple
from functools import total_ordering

logger = logging.getLogger("fc." + __name__)


class SimulationInfo(object):
    def __init__(self):
        """Things that would be global variables, except that we want this to be thread-safe


        """
        self.updateCount = 0
        self.theParameters = None
        self.runDesc = None
        self.followBank = None
        self.basicGraph = None
        self.tString = None
        self.economyDirectory = {}
        self.bankDirectory = {}
        # Have a network of banks. The (directed) edges are interbank loans.
        self.loanNetwork = nx.DiGraph()

        # banks are also connected if they have asset holdings in common. We have a bipartite graph, with edges
        # between assets and banks. There is an edge for each holding.
        self.assetNetwork = nx.Graph()
        self.lastId = 0

    def __repr__(self):
        return "<SimulationInfo %r: %s>" % (self.runDesc, self.updateCount)

    def clear(self):
        self.updateCount = 0
        self.theParameters = None
        self.runDesc = None
        self.followBank = None
        self.basicGraph = None
        self.tString = None

        self.economyDirectory.clear()
        self.bankDirectory.clear()
        self.loanNetwork = nx.DiGraph()
        self.assetNetwork = nx.Graph()

    def get_banks(self):
        """ Get a list of banks, always in the same order


        @return:
        """
        return sorted(self.bankDirectory.values())

@total_ordering
class SimulationObject(object):
    """Base class for objects used in the simulation.

    All simulation objects have a unique id and a name.
    They are totally ordered by their id (this makes sorting lists of them easy)

    """

    def __init__(self, simInfo, name):
        self.simInfo = simInfo
        self.name = name
        simInfo.lastId += 1
        self.id_ = simInfo.lastId

    def __hash__(self):
        """Make simulation objects hashable, so they can be keys in the dictionary

        @return:
        """
        return hash(self.id_)

    def __repr__(self):
        return "<%s%r: %s>" % (self.__class__.__name__, self.id_, self.name)

    def __eq__(self, other):
        return (self.id_ == other.id_)

    def __lt__(self, other):
        return (self.id_ < other.id_)


class ProportionError(Exception):
    """Exception raised when a proportion is outside [0, 1]
    """


class ParameterError(Exception):
    """Exception raised when there's a problem with parameters
    """


class UniqueError(Exception):
    """Exception raised when there's a uniqueness problem
    """


BankHistory = namedtuple('BankHistory', 'balanceSheets borrowings defaults')
InvestmentHistory = namedtuple('InvestmentHistory', 'holdings prices')
HoldingRecord = namedtuple('HoldingRecord', 'when investmentId bankId amount')
PriceRecord = namedtuple('PriceRecord', 'when investmentId price')
BorrowingRecord = namedtuple('BorrowingRecord', 'when fromBankId toBankId amount')
DefaultRecord = namedtuple('DefaultRecord', 'when bankId ratio')
BalanceSheetRecord = namedtuple('BalanceSheetRecord', 'when bankId lending investments cash borrowing deposits capital')


class ParameterDefinitions(dict):
    """a dictionary of valid parameters, indexed by parameter name.

    the value is a pair. Element 1 is the type of the parameter, element 2 is what values are valid
    The validity is a list. If it's of length 2, it's the end points of a range. Otherwise, it lists the valid values.
    if it's None, or an empty list, all values are valid

    """

    def clear_definitions(self):
        self.clear()

    def add_definition(self, pName, pType, pValid=None):
        if pName in self:
            raise ParameterError("%s is already defined as a parameter" % pName)
        self[pName] = pType, pValid

    def get_type(self, pName):
        if not pName in self:
            raise ParameterError("%s is not a valid parameter name" % pName)
        return self[pName][0]

    def is_value_valid(self, pName, pVal):
        if not pName in self:
            raise ParameterError("%s is not a valid parameter name" % pName)
        pType = self[pName][0]
        if pType == "bool":
            if pVal is not True and pVal is not False:
                raise ParameterError("%r is not a valid value for %s: must be boolean " %
                                     (pVal, pName))
        elif not isinstance(pVal, pType):
            raise ParameterError("%r is not a valid value for %s: must be type %s but is %r" %
                                 (pVal, pName, pType, type(pVal)))
        pValid = self[pName][1]
        ans = True
        if pValid:   # there is validity information in the definition
            if len(pValid) == 2 and (pType == int or pType == float):
                ans = pValid[0] <= pVal <= pValid[1]
            else:
                ans = pVal in pValid
        return ans


class Parameters(object):
    def __init__(self, definitions=None, parent=None):
        if definitions is None:
            definitions = ParameterDefinitions()
        self.params = {}  # empty dictionary
        self.pDefs = definitions
        self.parent = parent  # default values

    def get(self, pName, default=None):
        """Get the value of the named parameter

        if the parameter isn't in this set of parameters, look in the parent set.
        if it can't be found anywhere, use the default value

        @param pName: parameter name
        @param default: default value
        @return:
        """
        if not pName in self.pDefs:
            raise ParameterError("%s is not a valid parameter name" % pName)
        ans = default
        if pName in self.params:
            ans = self.params[pName]
        elif self.parent:
            ans = self.parent.get(pName, default)
        return ans

    def set(self, pName, pVal):
        """Set the value of the named parameter

        @param pName: parameter name
        @param pVal: parameter value

        """
        if not pName in self.pDefs:
            raise ParameterError("%s is not a valid parameter name" % pName)

        pType = self.pDefs[pName][0]
        if pType == "bool":
            pVal = str2bool(pVal)
        else:
            pVal = pType(pVal)

        if self.pDefs.is_value_valid(pName, pVal):
            self.params[pName] = pVal
        else:
            raise ParameterError("%r is not a valid value for %s " % (pVal, pName))

    def get_params_from_pList(self, pList):
        """Get all the parameters in this list and add them to this parameter set

        Each parameter has a name and a value
        @param pList: the list of 3-tuples that are for the correct entity
        """
        for dType, dName, dVal in pList:
            if dType == 'parameter':
                self.set(dName, dVal)


def get_diverse_sample(population, diversity):
    """Get a sample from the population with the required diversity

    A diversity of 1 means get the whole population
    A diversity of 0 means get just one element
    Between 0 and 1, get a proportionate number
    @param population:
    @param diversity:
    @return:
    """
    if diversity < 0 or diversity > 1:
        raise ProportionError("Diversity must be between 0 and 1")
    elif diversity == 0:
        ans = random.choice(population)
    elif diversity == 1:
        ans = population[:]  # take a copy, just in case
    else:
        k = int(math.ceil(diversity * len(population)))
        ans = random.sample(population, k)
    return ans


def str2bool(v):
    if v.lower() in ['true', 't', '1', 'yes']:
        return True
    elif v.lower() in ['false', 'f', '0', 'no']:
        return False
    else:
        msg = "Can't convert %r to boolean " % v
        raise ValueError(msg)


def read_params_from_xml(root, fName):
    simParams = root.find('simulator')
    if simParams is None:
        msg = "No simulator parameters in %s" % fName
        logger.error(msg)
        raise ParameterError(msg)
    pList = get_params_from_xml('simulator', 'simulator', simParams)
    eList = get_entity_params_from_xml('economy', root, fName)
    pList += eList
    eList = get_entity_params_from_xml('bank', root, fName)
    pList += eList
    return pList


def read_params_file(paramsDir, fName):
    """Read an xml parameters file into a list of tuples

    Each tuple consists of the following:
    entityType      simulator, economy or bank
    entityName
    dataType        parameter or attribute
    dataName
    dataValue       a string
    @param fName:
    """
    tree = ET.parse(paramsDir + fName)
    pList = read_params_from_xml(tree.getroot(), fName)

    graphFile = None
    for eType, eName, dataType, dataName, dataValue in pList:
        if dataName == "graphFile":
            graphFile = dataValue
            break
    if graphFile is None:
        msg = "No graph file specified in %s" % fName
        logger.error(msg)
        raise ParameterError(msg)
    basicGraph = nx.read_gexf(paramsDir + graphFile)  # This gives us a graph of possible lending

    return pList, basicGraph


def get_entity_params_from_xml(eType, xmlElt, fName):
    entityList = xmlElt.findall(eType)
    if not entityList:
        msg = "No %s parameters in %s" % (eType, fName)
        logging.error(msg)
        raise ParameterError(msg)
    pList = []
    for e in entityList:
        eName = e.get('name')
        if not eName:
            msg = "A %s must have a name in %s" % (eType, fName)
            logging.error(msg)
            raise ParameterError(msg)
        eList = get_params_from_xml(eType, eName, e)
        pList += eList
    return pList


def get_params_from_xml(entityType, entityName, xmlElt):
    """Get all the time parameters hanging off the given element and add them to this parameter set

    Each parameter has a name and a value, and optionally a type, which is either 'int' or 'float'
    @param xmlElt: the root element for this set of parameters
    """
    pList = []
    for k, v in xmlElt.attrib.items():
        pList.append((entityType, entityName, 'attribute', k, v))
    for param in xmlElt.findall('parameter'):
        name = param.get('name')
        val = param.get('value')
        pList.append((entityType, entityName, 'parameter', name, val))
    return pList


def get_value_from_pList(pList, entityType, entityName, dataType, paramName):
    ans = None
    for eType, eName, dType, dName, dVal in pList:
        if eType == entityType and eName == entityName and dType == dataType and dName == paramName:
            ans = dVal
            break
    return ans
