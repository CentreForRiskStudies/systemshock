#!/usr/bin/python

import networkx as nx
import random
import math
from operator import attrgetter, itemgetter
import datetime


def noneToZero(value):
        return int(0 if value is None else value)

# NetworkX graph subclass with methods specific to the Supply Chain Modelling problem.
class supplyChainNetwork(nx.DiGraph):
    def __init__(self,name,simulationLength=100,data=None,**attr):
        nx.DiGraph.__init__(self, data=None, **attr)
        self.name = name
        self.health = 1.0
        self.simulationLength=simulationLength

    def __repr__(self):
        return "supplyChainNetwork(name=%r)" % (self.name)
    
    # Method for adding a product to the graph.
    def addProduct(self,product):
        if hasattr(self, 'productCatalogue'):
            self.productCatalogue.update({product:[]})
        else:
            self.productCatalogue = dict(product=[])

    # Method for adding an edge to the graph, updating the relevant nodes neighbour-knowledge.
    def add_edge(self,u, v, attr_dict=None, **attr):
        nx.DiGraph.add_edge(self,u,v,attr_dict,**attr)
        u.getNeighbours()
        v.getNeighbours()

    # Method for adding many products to the graph.
    def addProductCatalogue(self,productCatalogue):
        for product in productCatalogue:
            
            self.addProduct(product)

    # Method for adding many products and their stockists to the graph.
    def addProductStockistCatalogue(self,productStockistCatalogue):
        if hasattr(self, 'productCatalogue'):
            self.productCatalogue.update(productStockistCatalogue)

    # Method for (re)compiling the dictionary of stockists for each product.
    def checkStockists(self,productCatalogue):
        if hasattr(self, 'productCatalogue'):
            for node in self.nodes():
                
                for product in node.products:
                    
                    self.productCatalogue[product].append(node)
        else:
            pass
            #print ('Supply Chain Network ' + self + ' has no product catalogue.')
            #print 'No dictionary of stockists was created.'

    # Method to add a new stockist for a product.        
    def addStockist(self,product,newStockist):
        if hasattr(self, 'productCatalogue'):
            currStockists = self.productCatalogue.get(product,[])
            currStockists.append(newStockist)
            self.productCatalogue.update({product : currStockists})
        else:
            #print ('Supply Chain Network ' + self.name + ' has no product catalogue.')
            #print 'Calling addStockist may not be what you want to do'
            self.productCatalogue = dict(product=[newStockist])

    # Method for adding a node to the graph.
    def add_node(self, n, attr_dict=None, **attr):
        nx.DiGraph.add_node(self,n,attr_dict, **attr)

    def giveNodeContext(self):
        for node in self.nodes_iter():
            node.getGraphContext()
            if isinstance(node, supplyChainNode):
                for product in node.products:
                    self.addStockist(product,node)
    
    def orderedNodes(self):
        nameSortedNodes = sorted(self.nodes(), key=attrgetter('name'))
        tierSortedNodes = sorted(nameSortedNodes, key=attrgetter('depth'))
        return tierSortedNodes
    
    def moveShipments(self):
        for node1, node2 in self.edges():
            edata = self[node1][node2]
            if isinstance(edata,dict):
                for key in edata:
                    if isinstance(key,tuple):
                        if edata[key] is None:
                            continue
                        travelTime, quant, prod = edata[key]
                        edata[key]  = (travelTime + 1, quant, prod)
                for key, val in edata.items():
                    if val == None:
                        del self[node1][node2][key]
                    
    def calculateHealth(self):
        healthList = [node.calculateHealth() for node in self.nodes()]
        self.health = (sum([health**2 for health in healthList])/len(healthList))**0.5
        return self.health

    def makeTimeStep(self):
        nodeList = self.orderedNodes()
        moveShipments(self)
        #print '------------------------------------------'
        for node in nodeList:
            #print ''
            ## Ensure the node has been initialised properly.
            #if node.currentTime == 0:
            #    node.getGraphContext()
            #print node.name + ':'
            #print
            node.makeTimeStep()
        #print '------------------------------------------'
        self.calculateHealth()
        
# A product in the supply chain
class supplyChainProduct(object):
    def __init__(self,name,mass=1,warehouseSize=1,value=1,shippingSize=-1,
                 expires=False):
        self.name = name # (str) Name of the product.
        self.mass = mass # (int) Mass of the product.
        self.warehouseSize = warehouseSize # (int) Units of warehousing taken up by each product.
        self.value = value # (float) value of the product.
        self.shippingSize = shippingSize # (int) units of shipping space taken up by each product.
        if self.shippingSize == -1:
            self.shippingSize = self.warehouseSize
        self.stockists = dict() 
        self.myHash = hash((self.name, self.mass)) # tuple-hash for when using as a key in a dictionary.
    
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.myHash == other.myHash
    
    def __ne__(self, other):
        return not self.__eq__(self, other)
    
    def __hash__(self):
        return self.myHash
    
    def __repr__(self):
        return "supplyChainProduct(name=%r , value = %r)" % (self.name,self.value)
    
    def getStockists(self,supplyChainNetwork):
        self.stockists[supplyChainNetwork] = supplyChainNetwork.productCatalogue.get(self)
        if self.stockists[supplyChainNetwork] == None:
            self.stockists[supplyChainNetwork] = []
        return self.stockists[supplyChainNetwork]


def findPrevValueRecur(dictionary, targetNode, product, startTime):
    " Starting at startTime, goes to dictionary to find the most \
    recent value recorded for targetNode and product."
    assert startTime >= 0
    currDict = dictionary[startTime]
    prevVal = currDict.get((targetNode,product),False)
    if prevVal is False and startTime == 0:
        return None, 0
    elif prevVal is False:
        return findPrevValueRecur(dictionary, targetNode, product, startTime -1)
    else:
        return prevVal, startTime
    
def findNextValueRecur(dictionary, targetNode, product, startTime):
    " Starting at startTime, goes to dictionary to find the most \
    recent value recorded for targetNode and product"
    assert startTime >= 0 and startTime <= targetNode.supplyChain.simulationLength
    currDict = dictionary[startTime]
    nextVal = currDict.get((targetNode,product),False)
    if (nextVal is False) and (startTime > targetNode.currentTime):
        return None, targetNode.currentTime + 1
    elif nextVal is False:
        return findNextValueRecur(dictionary, targetNode, product, startTime +1)
    else:
        return nextVal, startTime


# Update aggregate records
def updateAggregatesPersistent(thisNode,dictionary,currentTime,targetNode,product,quantity):
    "Updates aggregate records for dictionaries where old values should be carried forward \
    i.e. values which persist across time periods, e.g. outstanding orders."
    
    # Update nodes aggregate
    prevValue = noneToZero(findPrevValueRecur(dictionary,'allNodes',product,currentTime)[0])
    dictionary[currentTime][('allNodes',product)] = prevValue + quantity
   
    # Update products aggregate
    prevValue = noneToZero(findPrevValueRecur(dictionary,targetNode,'allProducts',currentTime)[0])
    dictionary[currentTime][(targetNode,'allProducts')] = prevValue + quantity
    
    # Update total aggregate
    prevValue = noneToZero(findPrevValueRecur(dictionary,'allNodes','allProducts',currentTime)[0])
    dictionary[currentTime][('allNodes','allProducts')] = prevValue + quantity
    

# Update aggregate records
def updateAggregatesTemporal(thisNode,dictionary,currentTime,targetNode,product,quantity):
    "Updates aggregate records for dictionaries where old values should NOT be carried forward."
    # Final entry in array is used to store aggregates over time.
    # Update time aggregates
    SIMULATION_LENGTH = thisNode.supplyChain.simulationLength
    prevValue = dictionary[SIMULATION_LENGTH].get((targetNode,product),0)
    dictionary[SIMULATION_LENGTH][(targetNode, product)] = prevValue + quantity
    # Get the dictionary for the current time period
    currDict = dictionary[currentTime]
    # Update nodes aggregate
    prevValue = currDict.get(('allNodes',product),0)
    dictionary[currentTime][('allNodes',product)] = prevValue + quantity
    # Update node/time aggregates
    prevValue = dictionary[SIMULATION_LENGTH].get(('allNodes',product),0)
    dictionary[SIMULATION_LENGTH][('allNodes',product)] = prevValue + quantity
    # Update products aggregate
    prevValue = currDict.get((targetNode,'allProducts'),0)
    dictionary[currentTime][(targetNode,'allProducts')] = prevValue + quantity
    # Update product/time aggregates
    prevValue = dictionary[SIMULATION_LENGTH].get((targetNode,'allProducts'),0)
    dictionary[SIMULATION_LENGTH][(targetNode,'allProducts')] = prevValue + quantity
    # Update node/product aggregate
    prevValue = currDict.get(('allNodes','allProducts'),0)
    dictionary[currentTime][('allNodes','allProducts')] = prevValue + quantity
    # Update node/product/time aggregates
    prevValue = dictionary[SIMULATION_LENGTH].get(('allNodes','allProducts'),0)
    dictionary[SIMULATION_LENGTH][('allNodes','allProducts')] = prevValue + quantity

# Class for the actors in the supply chain


        
class supplyChainNode(object):
    def __init__(self, *args, **kwargs):
        
        # Process mandatory arguments
        self.name = str(args[0]) # (str) label string to refer to the node (also used for hashing).
        self.supplyChain = args[1] # (supplyChainNetwork) Supply Chain the node belongs to.
        assert isinstance(self.supplyChain, supplyChainNetwork)
        self.targetInventory = args[2] # (dict) All products the node deals with, and their target stock levels.
        self.storageCapacity = args[3] # (int) Size of warehousing facility.
        self.products = [prod for prod in self.targetInventory]
        self.simulationLength = self.supplyChain.simulationLength
        
        # Process optional arguments
        self.longName = kwargs.get('popup')
        self.tier = kwargs.get('tier')
        self.storageInUse = kwargs.get('initialStorageUsed',0) # (int) Volume of warehousing space currently in use.
        self.currentTime = kwargs.get('currentTime',0) # (int) Time at which to initialize node, defaults to 0.
        self.minOrder = {prod: (kwargs.get('minOrder',dict())).get(prod, 0) for prod in self.products} # (dict) Minimum order accepted, keyed by product. Defaults to 0.
        self.processingCapacity = kwargs.get('processingCapacity',dict()) # (dict) Units that can be built in each time period, keyed by product.
        self.label = kwargs.get('label',self.name)
        try:
            self.buildInstructions = {prod : (kwargs.get('buildInstructions',dict()))[prod] for prod in self.processingCapacity }
        except KeyError:
            #print 'Every product for which a processingCapacity is defined must\
                    #have a recipe present in buildInstructions'
            raise
        
        
        # Initialise some attributes for record keeping.
        self.inventory = [dict() for x in range(self.simulationLength + 1)] # Inventory array (by time) of dicts (each keyed by product)
        self.oldestOrder = dict((product, dict()) for product in self.products) # Dict of dicts, first keyed on product, second keyed on node. Stores time of oldest outstanding orders
        self.oldestOrderLastCall = -1 # Currently unused, potential optimisation
        self.myHash = hash((self.name, self.supplyChain.name)) # To allow use as keys in dictionaries, etc.
        self.unitsBuilt = [dict() for x in range(self.simulationLength + 1)] # Record of number of units built.
        self.overstock = [dict() for x in range(self.simulationLength + 1)] # Record of items discarded due to lack of warehousing.
        self.salesLost = [dict() for x in range(self.simulationLength + 1)] # Record of sales lost due to lack of inventory.
        self.stockistPreferences = dict((product,dict()) for product in self.products)
        
        self.depth = None
        self.health = 1.0
        
        # Initialise current stock to safety threshold
        for product in self.products:
            self.inventory[self.currentTime][product] = self.targetInventory.get(product,0)
            self.storageInUse += self.targetInventory.get(product,0)*product.warehouseSize
            # Let supplyChainNetwork know you are a stockist for /product/
            # self.supplyChain.addStockist(product,self)

        # Initialise core dictionaries for record keeping
        self.ordersMade = [dict() for x in range(self.simulationLength + 1)]
        self.downstreamOutstanding = [dict() for x in range(self.simulationLength + 1)]
        self.shipmentsReceived = [dict() for x in range(self.simulationLength + 1)]
        self.ordersReceived = [dict() for x in range(self.simulationLength + 1)]
        self.upstreamOutstanding = [dict() for x in range(self.simulationLength + 1)]
        self.shipmentsMade = [dict() for x in range(self.simulationLength + 1)]
        self.unitsSold = [dict() for x in range(self.simulationLength + 1)]

    # Human readable __repr__
    def __repr__(self):
        return "supplyChainNode([%r,%r,%r,%r])" % (self.name, self.supplyChain, self.targetInventory, self.storageCapacity)

    # The following 3 functions are defined to allow supplyChainNodes to be used as keys in dictionaries
    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.myHash == other.myHash
    def __ne__(self, other):
        return not self.__eq__(other)
    def __hash__(self):
        return self.myHash  

    # It is essential that this method is run after the node is added to the graph, and before any simulation!
    # The add_node method defined in the class supplyChainNetwork should take care of that.
    def getGraphContext(self):
        
        # Note the slightly unintuitive convention. This is because edges point in direction of shipments
        # whereas, in a market driven model, one tends to think of upstream and downstream in terms of orders.
        self.upstream = self.supplyChain.successors(self)
        self.downstream = self.supplyChain.predecessors(self)
        for neighbour in self.upstream:
            if isinstance(neighbour, supplyChainRetailMarket):
                self.depth = 1
            elif neighbour.depth:
                if self.depth:
                    self.depth = min(self.depth, neighbour.depth+ 1)
                else:
                    self.depth = neighbour.depth + 1
                    
        if self.depth == 1:
            markets = [node for node in self.upstream if isinstance(node, supplyChainRetailMarket)]
            for market in markets:
                for product in self.products:
                    self.salesLost[self.currentTime][(market, product)] = 0
                    self.salesLost[self.simulationLength][(market, product)] = 0
                    updateAggregatesTemporal(self,self.salesLost,self.currentTime,market,product,0)
                
        
        # Initialize stored history dictionaries.
        for product in self.products:
            self.unitsBuilt[self.currentTime][product] = 0
            self.overstock[self.currentTime][product]  = 0
            for downstreamNode in self.downstream:
                self.ordersMade[self.currentTime][( downstreamNode ,product)] = 0
                self.ordersMade[self.simulationLength][( downstreamNode ,product)] = 0
                self.downstreamOutstanding[self.currentTime][( downstreamNode ,product)] = 0
                self.shipmentsReceived[self.currentTime][( downstreamNode ,product)] = 0
                self.shipmentsReceived[self.simulationLength][( downstreamNode ,product)] = 0
                # Create product aggregates.
                self.ordersMade[self.currentTime][(downstreamNode ,'allProducts')] = 0
                self.ordersMade[self.simulationLength][(downstreamNode ,'allProducts')] = 0
                self.downstreamOutstanding[self.currentTime][(downstreamNode ,'allProducts')] = 0
                self.shipmentsReceived[self.currentTime][(downstreamNode ,'allProducts')] = 0
                self.shipmentsReceived[self.simulationLength][(downstreamNode ,'allProducts')] = 0
            for upstreamNode in self.upstream:    
                self.ordersReceived[self.currentTime][(upstreamNode ,product)] = 0
                self.ordersReceived[self.simulationLength][(upstreamNode ,product)] = 0
                self.upstreamOutstanding[self.currentTime][(upstreamNode ,product)] = 0
                self.shipmentsMade[self.currentTime][(upstreamNode ,product)] = 0
                self.shipmentsMade[self.simulationLength][(upstreamNode ,product)] = 0
                # Create product aggregates.
                self.ordersReceived[self.currentTime][(upstreamNode ,'allProducts')] = 0
                self.ordersReceived[self.simulationLength][(upstreamNode ,'allProducts')] = 0
                self.upstreamOutstanding[self.currentTime][(upstreamNode ,'allProducts')] = 0
                self.shipmentsMade[self.currentTime][(upstreamNode ,'allProducts')] = 0
                self.shipmentsMade[self.simulationLength][(upstreamNode ,'allProducts')] = 0
            # Create node aggregates.
            self.ordersMade[self.currentTime][('allNodes',product)] = 0
            self.ordersMade[self.simulationLength][('allNodes',product)] = 0
            self.downstreamOutstanding[self.currentTime][('allNodes',product)] = 0
            self.shipmentsReceived[self.currentTime][('allNodes',product)] = 0
            self.shipmentsReceived[self.simulationLength][('allNodes',product)] = 0
            self.ordersReceived[self.currentTime][('allNodes',product)] = 0
            self.ordersReceived[self.simulationLength][('allNodes',product)] = 0
            self.upstreamOutstanding[self.currentTime][('allNodes',product)] = 0
            self.shipmentsMade[self.currentTime][('allNodes',product)] = 0
            self.shipmentsMade[self.simulationLength][('allNodes',product)] = 0
        # Create node+product aggregates.
        self.ordersReceived[self.currentTime][('allNodes','allProducts')] = 0
        self.ordersReceived[self.simulationLength][('allNodes','allProducts')] = 0
        self.upstreamOutstanding[self.currentTime][('allNodes','allProducts')] = 0
        self.shipmentsMade[self.currentTime][('allNodes','allProducts')] = 0
        self.shipmentsMade[self.simulationLength][('allNodes','allProducts')] = 0
        self.ordersMade[self.currentTime][('allNodes','allProducts')] = 0
        self.ordersMade[self.simulationLength][('allNodes','allProducts')] = 0
        self.downstreamOutstanding[self.currentTime][('allNodes','allProducts')] = 0
        self.shipmentsReceived[self.currentTime][('allNodes','allProducts')] = 0
        self.shipmentsReceived[self.simulationLength][('allNodes','allProducts')] = 0
        
    # Add a new product to the node.
    def addProduct(self,product,quantity=0):
        self.products.append(product)
        self.inventory[self.currentTime][product] = quantity
        self.graph.addStockist(product,self)
        for downstreamNode in self.downstream:
            self.ordersMade[self.currentTime][(downstreamNode ,product)] = 0
            self.downstreamOutstanding[self.currentTime][(downstreamNode ,product)] = 0
            self.shipmentsReceived[self.currentTime][(downstreamNode ,product)] = 0
        for upstreamNode in self.upstream:
            self.ordersReceived[self.currentTime][(upstreamNode ,product)] = 0
            self.upstreamOutstanding[self.currentTime][(upstreamNode ,product)] = 0
            self.shipmentsMade[self.currentTime][(upstreamNode ,product)] = 0
        
    
    # Query the graph for the node's neighbours            
    def getNeighbours(self):
        self.upstream = (self.supplyChain).successors(self)
        self.downstream = (self.supplyChain).predecessors(self)

    # Calculate available storage  
    def getAvailableStorage(self):
        return self.storageCapacity - self.storageInUse
    
    # Receive an order from an upstream node
    def receiveOrder(self,originNode,quantity,product):
        #print("Node %r receiving order of %r units of %r from %r" % (self, quantity, product, originNode))
        if quantity > self.minOrder[product]:
            self.ordersReceived[self.currentTime][(originNode,product)] = quantity
            updateAggregatesTemporal(self,self.ordersReceived,self.currentTime,originNode,product,quantity)
            previouslyOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding, originNode, product, self.currentTime)[0])
            self.upstreamOutstanding[self.currentTime][(originNode,product)] = previouslyOutstanding + quantity
            updateAggregatesPersistent(self,self.upstreamOutstanding,self.currentTime,originNode,product,quantity)
        else:
            pass
            #print('Node ' + originNode.name + ' attempted to order ' + str(quantity) + ' units of ' + product.name + ', fewer than the minimum order (' +str(self.minOrder[product]) + ') for ' + self.name + '.')
            #print('Order cancelled.')
    
    # Make an order to a downstream node
    def makeOrder(self,targetNode,quantity,product):
        #print("Node %r making order of %r units of %r to %r" % (self, quantity, product, targetNode))
        assert quantity > 0
        threshold = targetNode.minOrder[product]
        if quantity > threshold:
            targetNode.receiveOrder(self,quantity,product)
            prevValue = self.ordersMade[self.currentTime].get((targetNode,product),0)
            self.ordersMade[self.currentTime][(targetNode,product)] = prevValue + quantity
            updateAggregatesTemporal(self,self.ordersMade,self.currentTime,targetNode,product,quantity)
            previousValue = noneToZero(findPrevValueRecur(self.downstreamOutstanding, targetNode, product, self.currentTime)[0])
            self.downstreamOutstanding[self.currentTime][(targetNode,product)] = previousValue + quantity
            updateAggregatesPersistent(self,self.downstreamOutstanding,self.currentTime,targetNode,product,quantity)
        else:
            pass
            #print('Node ' + self.name + ' attempted to order ' +str(quantity) + 'units of ' + product.name + ',fewer than the minimum order (' + str(targetNode.minOrder[product]) + ') for ' + targetNode.name  + '.')
    
    # Make a shipment to an upstream node
    def makeShipment(self,targetNode,quantity,product):
        # Make sure sufficient product exists
        #print("Making shipment of %r units of %r to %r" % (quantity, product, targetNode))
        assert quantity > 0
        if quantity > self.inventory[self.currentTime][product]:
            #print 'Attempted to ship more stock than currently available in inventory'
            #print 'Shipment cancelled'
            return False
        elif not targetNode in self.upstream:
            if not targetNode in self.supplyChain.successors(self):
                #print 'Attempted to ship to a node without a valid edge in place'
                #print 'Shipment cancelled'
                #print "N.B. getNeighbours() can be used to update a node's knowledge of its neighbours"
                return False
            else:
                self.getNeighbours()
        else:
            # Place the shipment on the edge
            # Note how shipments are stored on an edge:{(timeWhenShipped, origin, target) : (timeOnEdge,quantity,product)}
            self.supplyChain.add_edge(self, targetNode, {(self.currentTime,self,targetNode):(0,quantity,product)})
            self.inventory[self.currentTime][product] -= quantity
            # Update the outstanding orders
            previouslyOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding, targetNode, product, self.currentTime-1)[0])
            self.upstreamOutstanding[self.currentTime][(targetNode,product)] = previouslyOutstanding - quantity
            updateAggregatesPersistent(self,self.upstreamOutstanding,self.currentTime,targetNode,product,-quantity)
            self.shipmentsMade[self.currentTime][(targetNode,product)] = quantity
            updateAggregatesTemporal(self,self.shipmentsMade,self.currentTime,targetNode,product,quantity)
            self.storageInUse -= quantity*(product.warehouseSize)
            return True
    
    # Finds the time period of the oldest outstanding order from /node/
    # returns the outstanding quantity and the period in which it was ordered.
    def findOldestOutstandingOrder(self,node,product,startTime):
        assert self.shipmentsMade[self.simulationLength][(node,product)] <= self.ordersReceived[node.supplyChain.simulationLength][(node,product)]
        quantity, orderTime = findNextValueRecur(self.ordersReceived, node, product, 0)
        shipment, shipmentTime = findNextValueRecur(self.shipmentsMade, node, product, 0)
        while shipment and (shipmentTime < self.currentTime + 1):
            quantity -= shipment
            if quantity <= 0:
                nextOrder = findNextValueRecur(node.ordersMade, self, product, orderTime)
                if nextOrder:
                    quantity  += nextOrder[0]
                    orderTime = nextOrder[1]
                else:
                    quantity = None
                    orderTime = self.currentTime
            shipment, shipmentTime = findNextValueRecur(self.shipmentsMade, node, product, shipmentTime)
        return (quantity, orderTime)
    
    def hasOrdersOutstanding(self,targetNode,product,time):
        if targetNode in self.upstream:
            if findPrevValueRecur(self.upstreamOutstanding, targetNode, product, time)[0] > 0:
                return True
            else:
                return False
        if targetNode in self.downstream:
            if findPrevValueRecur(self.downstreamOutstanding, targetNode, product, time)[0] > 0:
                return True
            else:
                return False
        else:
            return False
    
    # Make shipments of /product/ according to order in which orders were placed.
    def makeAllProductShipments(self,product):
        totalOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding,'allNodes',product,self.currentTime+1)[0])
        # Check there are some orders to fulfil!
        if totalOutstanding == 0:
            return 
        # Check there is any stock to fill orders with
        if self.inventory[self.currentTime][product] == 0:
            return
        # If we have enough product to fulfill all orders, do so
        currInventory = self.inventory[self.currentTime].get(product,0)
        if currInventory >= totalOutstanding:
            for node in self.upstream:
                currOutstanding = findPrevValueRecur(self.upstreamOutstanding,node,product,self.currentTime)[0]
                if currOutstanding > 0:
                    self.makeShipment(node, currOutstanding, product)
        # Otherwise, fulfil those orders that one can, starting with the oldest.
        else:
            # Keep going until no more outstanding orders or no more inventory
            while self.inventory[self.currentTime][product] > 0 and totalOutstanding > 0:
                # Only look at nodes with some outstanding orders
                nodesToCheck = [ node for node in self.upstream if self.hasOrdersOutstanding(node,product,self.currentTime)]
                # Don't bother with the following rigmarole unless there's >1 upstream neighbour!
                if len(nodesToCheck)>1:
                    # Go through all nodes to find who should get priority
                    priorityNode = None
                    for node in nodesToCheck:
                        #print("Considering node %r in attempts to find oldest outstanding order" % (node))
                        oldestOrders = self.oldestOrder[product]
                        oldestOrders[node] = self.findOldestOutstandingOrder(node, product, 0)
                        self.oldestOrderLastCall = self.currentTime
                        noBest = [(0, self.currentTime), None]
                        candBest = oldestOrders[node]
                        (oldBestQuant, oldBestTime), priorityNode  = oldestOrders.get('allNodes',noBest)
                        if candBest[1] < oldBestTime:
                            oldestOrders['allNodes'] = [candBest, node]
                            priorityNode = node
                        elif (candBest[0] == oldBestTime
                            and candBest[1] > oldBestQuant):
                            oldestOrders['allNodes'] = [candBest, node]
                            priorityNode = node
                        elif (priorityNode and
                              candBest[0] == oldBestTime and
                              candBest[1] == oldBestQuant and
                              self.ordersReceived[self.simulationLength][(node,product)] >
                              self.ordersReceived[self.simulationLength].get((priorityNode,product),0) ):
                            oldestOrders['allNodes'] = [candBest, node]
                            priorityNode = node
                    # Having found the oldest order, fulfil in totality if possible.
                    outstandingOld = oldestOrders.get('allNodes',[0])[0]
                    if outstandingOld < 1:
                        #print "Less than 1"
                        #print "Current inventory of %r, totalOutstanding %r" % (self.inventory[self.currentTime][product], totalOutstanding)
                        #print "Currently oustanding to %r: %r" % (node, self.upstreamOutstanding[self.currentTime][(node,product)])
                        continue
                    elif priorityNode == None:
                        pass
                        #print "No priority node."
                    shipmentSize = min(currInventory, outstandingOld)
                    if not self.makeShipment(priorityNode, shipmentSize, product):
                        continue
                    #print(self.name + ' shipped ' + str(shipmentSize) + ' units of ' + product.name + 'to ' + priorityNode.name +'.')
                else:
                    prodRemaining = self.inventory[self.currentTime][product]
                    self.makeShipment(nodesToCheck[0],prodRemaining,product)
                    #print(self.name + ' shipped ' + str(prodRemaining) + ' units of ' + product.name + ' to its sole upstream neighbour, ' + self.upstream[0].name +'.')

    # Make shipments of all products
    def makeAllShipments(self):
        for product in self.products:
            self.makeAllProductShipments(product)
            
    
    def nStepHistoryAverage(self,numSteps,dictionary,targetNode,product,startTime):
        currValue = findPrevValueRecur(self.dictionary,targetNode,product,startTime)[0] 
        
    
    # Calculate the product deficit
    def calculateDeficit(self, product):
        currDemand = findPrevValueRecur(self.upstreamOutstanding, 'allNodes', product, self.currentTime)[0]
        currInven = self.inventory[self.currentTime].get(product,0)
        # Assume orders will 'come good'. Could add a coefficient x in (0,1] to represent reliability.
        incomingInven = findPrevValueRecur(self.downstreamOutstanding, 'allNodes', product, self.currentTime)[0]
        try:
            directDeficit = currDemand - currInven -incomingInven
        except TypeError:
            #print 'calculateDeficit encountered a type error when calculating directDeficit, \
            #    probably from None values introduced by findPrevValueRecur. \
            #    Converting potential None values to zero.'
            currDemand = noneToZero(currDemand)
            incomingInven = noneToZero(incomingInven)
            directDeficit = currDemand - currInven -incomingInven
        implicitDeficit = 0
        for complexProduct in self.buildInstructions:
            multiplier = self.buildInstructions[complexProduct].get(product,0)
            if multiplier > 0:
                currDemand = findPrevValueRecur(self.upstreamOutstanding, 'allNodes', complexProduct, self.currentTime)[0]
                currInven = self.inventory[self.currentTime][complexProduct]
                incInven = findPrevValueRecur(self.downstreamOutstanding,'allNodes',complexProduct,self.currentTime)[0]
                try:
                    complexProductDeficit = currDemand - currInven - incInven
                except TypeError:
                    print ('calculateDeficit encountered a type error when calculating complexProductDeficit\
                       probably from None values introduced by findPrevValueRecur. \
                        Converting potential None values to zero.' )
                    currDemand = noneToZero(currDemand)
                    incInven = noneToZero(incInven)
                    complexProductDeficit = currDemand - currInven - incInven
                implicitDeficit += max(complexProductDeficit,0)*multiplier
        totalDeficit = max(directDeficit + implicitDeficit + self.targetInventory.get(product,0),0)
        return totalDeficit
    
    # Make orders of /product/ according to predicted need
    def makeAllProductOrders(self,product):
        suppliers = [node for node in self.downstream if product in node.products]
        unitsRequired = self.calculateDeficit(product)
        if unitsRequired == 0:
            return True
        if unitsRequired < 0:
            raise Exception('Something has gone wrong with calculateDeficit, it has returned a negative value.')
        if len(self.stockistPreferences.get(product,[])) == 0:
            # print 'No stockist preferences found, sharing orders equally'
            numSuppliers = len(suppliers)
            if numSuppliers == 0:
                #print 'No suppliers for product: ' + product.name
                return False
            for supplier in suppliers:
                self.stockistPreferences[product][supplier] = 1.0
        productStockistPrefs = self.stockistPreferences.get(product, None)
        if productStockistPrefs:
            shareTotal = 0
            for supplier in suppliers:
                shareTotal += productStockistPrefs[supplier] 
            for supplier in suppliers:
                supplierShare = productStockistPrefs[supplier]/float(shareTotal)
                orderSize = round(supplierShare*float(unitsRequired),0)
                if orderSize > supplier.minOrder[product]:
                    self.makeOrder(supplier,round(unitsRequired*supplierShare,0),product)
            return True
        else:
            #print 'Something has gone wrong with the stockist preferences.'
            return False
    
    # Make orders for all products
    def makeAllOrders(self):
        complexProducts = [product for product in self.buildInstructions if product in self.products]
        atomicProducts = [product for product in self.products if not product in complexProducts]
        for complexProduct in complexProducts:
            self.makeAllProductOrders(complexProduct)
        for atomicProduct in atomicProducts:
            self.makeAllProductOrders(atomicProduct)


    # Receive and store product
    def receiveShipment(self,originNode,timeWhenShipped,quantity,product):
        #print("Node %r receiving shipment of %r units of %r from node %r" % (self, quantity, product, originNode))
        previouslyOutstanding = noneToZero(findPrevValueRecur(self.downstreamOutstanding, originNode, product, self.currentTime)[0])
        self.downstreamOutstanding[self.currentTime][(originNode,product)] = previouslyOutstanding - quantity
        updateAggregatesPersistent(self,self.downstreamOutstanding,self.currentTime,originNode,product,-quantity)
        self.shipmentsReceived[self.currentTime][(originNode,product)] = quantity
        updateAggregatesTemporal(self,self.shipmentsReceived,self.currentTime,originNode,product,quantity)
        # Check there is room to store the new products
        if self.getAvailableStorage() > quantity*(product.warehouseSize):
            self.storageInUse += quantity*(product.warehouseSize)
        else:
            # If not, store what we can and record any losses
            self.storageInUse = self.storageCapacity
            productKept = int(self.getAvailableStorage()/product.warehouseSize)
            self.overstock[self.currentTime][product] = max(quantity - productKept,0)
            #print("Not enough warehouse space,  discarding %r units of %r" % (quantity - productKept, product))
        self.supplyChain.add_edge(originNode, self, {(timeWhenShipped,originNode,self): (-self.simulationLength,quantity,product)})

    # Unpack recently stored products
    def unpackShipments(self):
        # There are no past shipments in this case!
        if not self.currentTime > 0:
            return
        # Add shipments to inventory (after some delay)
        currentInventory = self.inventory[self.currentTime]
        for product in self.products:
            for node in self.downstream:
                # If received yesterday, add to inventory today.
                # Variable 'unpacking' times could be implemented as an attribute.
                boxed = self.shipmentsReceived[self.currentTime -1].get((node,product),0)
                currentInventory[product] = currentInventory.get(product,0) + boxed

    # Build products according to recipes
    def buildProducts(self):
        for key, value in self.buildInstructions.iteritems():
            if len(value) > 1:
                break
        else:
            return
        currentInventory = self.inventory[self.currentTime]
        # Build priority is according to dictionary order (i.e. pretty much random!)
        # N.B. If we want slightly less greedy production, change actual
        # inventory check to target inventory check.
        for product in self.buildInstructions:
            componentMax = []
            # Find the limiting factor in production by dividing current stock by number in recipe
            for componentProduct in self.buildInstructions[product]:
                componentStock = currentInventory.get(componentProduct,0)
                numInBuild = self.buildInstructions[product][componentProduct]
                try:
                    componentMax.append(int(componentStock/numInBuild))
                except ZeroDivisionError:
                    #print ('Do not put zero-use components in to build instructions!')
                    raise
            # Produce as many as possible, updating records accordingly
            newProducts = min(self.processingCapacity[product], min(componentMax))
            self.unitsBuilt[self.currentTime][product] = newProducts
            #print "%d units of %s built." % (newProducts, product)
            currentInventory[product] = currentInventory.get(product,0) + newProducts
            for componentProduct in self.buildInstructions[product]:
                currentInventory[componentProduct] = currentInventory.get(componentProduct,0)
                currentInventory[componentProduct] -= newProducts*self.buildInstructions[product][componentProduct]
                if currentInventory[componentProduct] < 0:
                    raise Exception('WHAT?! buildProducts is broken, check arithmetic for num new products produced.')

    # Do the daily chores (irrespective of orders, etc.)
    def updateInventory(self):
        assert self.currentTime > 0
        previousInventory = self.inventory[self.currentTime-1].copy()
        for product, quantity in previousInventory.iteritems():
            #print ("Updating inventory of %r to be %r" % (product, quantity))
            self.inventory[self.currentTime][product] = quantity
        self.unpackShipments()
        self.buildProducts()
        
    
    # UNFINISHED Method to forecast time of delivery
    def forecastDeliveries(self,product,futureTime,historylength=14):
         # Nodes which are supplying this product
        supplyingNodes = []
        supplyingNodes.append(node for node in self.downstream if node in product.getStockists(self.suplpyChain))
        for node in supplyingNodes:
            pass
    
    # Make a sale!
    def makeSale(self,market,product,quantity):
        currInven = self.inventory[self.currentTime].get(product,0)
        if currInven >= quantity:
            #print str(quantity) + ' units of ' + product.name + ' sold at ' + self.name
            self.ordersReceived[self.currentTime][(market,product)]=quantity
            updateAggregatesTemporal(self,self.ordersReceived,self.currentTime,market,product,quantity)
            self.inventory[self.currentTime][product] -= quantity
            self.shipmentsMade[self.currentTime][(market,product)] = quantity
            updateAggregatesTemporal(self,self.shipmentsMade,self.currentTime,market,product,quantity)
            self.supplyChain.add_edge(self,market,{(self.currentTime,self,market):(0,quantity,product)})
            self.unitsSold[self.currentTime][product] = quantity
            self.unitsSold[self.simulationLength][product] = self.unitsSold[self.simulationLength].get(product,0) + quantity
            return 1
        else:
            try:
                shortfall = quantity - currInven
                self.salesLost[self.currentTime][(market,product)] = shortfall
                updateAggregatesTemporal(self, self.salesLost, self.currentTime,market,product,shortfall)
                self.makeSale(market,product,currInven)
            except TypeError:
                #print product, currInven
                raise
            return float(currInven)/quantity
    
    # Check for shipments that have arrived
    def checkForShipments(self):
        ' Looks at all incoming edges and checks for any shipments that have \
        spent the requisite time on the edge to arrive'
        for downstreamNode in self.downstream:
            edata = self.supplyChain[downstreamNode][self]
            if isinstance(edata,dict):
                for key in edata:
                    if isinstance(key,tuple) and not (edata[key] is None):
                        if edata[key][0] >= edata.get('timeToTraverse',0):
                            quant, prod = edata[key][1:3]
                            timeWhenShipped = key[0]
                            originNode = key[1]
                            if key[2] == self:
                                self.receiveShipment(originNode,timeWhenShipped, quant, prod)
                            # An 'else' clause here could deal with routing shipments to other nodes!
        
    # Calculate the node health
    def calculateHealth(self):
        ''' Returns a crude metric of node health '''
        prodHealth = []
        for product in self.products:
                target = self.targetInventory[product]
                stockScore = max(1 - (abs(self.inventory[self.currentTime][product] - target)/target),0)
                prodHealth.append(stockScore)
        meanScore = (sum([x**2 for x in prodHealth])/len(prodHealth))**0.5
        self.health = meanScore
        return self.health
    
    def getHealth(self):
        return self.health

    # Make a timestep
    def makeTimeStep(self):
        self.getNeighbours()
        self.currentTime += 1
        self.updateInventory()
        self.checkForShipments()
        self.makeAllShipments()
        self.makeAllOrders()
        self.health = self.calculateHealth()


# Retail market object
class supplyChainRetailMarket(object):
    def __init__(self,*args,**kwargs):
        self.name = args[0]
        self.tier = -100
        self.supplyChain = args[1]
        self.simulationLength = self.supplyChain.simulationLength
        self.product = args[2]
        self.initialDemand = args[3]
        self.products = []
        self.currentTime = kwargs.get('startTime',0)
        self.marketDemand = [self.initialDemand for __ in range(self.simulationLength)]
        self.seed = kwargs.get('rngSeed',0)
        self.marketShare = kwargs.get('marketShare',None)
        self.label = self.name
        self.longName = kwargs.get('name','Missing longName')
        # Market reputation probably a better term
        if self.marketShare is None:
            self.marketShare = [dict() for __ in range(self.simulationLength)]
        self.ordersMade = [dict() for __ in range(self.simulationLength+1)]
        self.downstreamOutstanding = [dict() for __ in range(self.simulationLength)]
        self.shipmentsReceived= [dict() for __ in range(self.simulationLength+1)]
        self.upstream = []
        self.downstream = []
        self.depth = 0
        self.health = 1.0 

    def __repr__(self):
        return ("supplyChainRetailMarket(name=%r,currDemand=%r)" 
            % (self.name, self.marketDemand[self.currentTime]))

    def poissonPDF(x,mu):
        return math.exp(x*math.log(mu) - mu - math.lgamma(x))
    
    # Get poisson random num
    def getMarketDemand(self,prev_value):
        return max(math.ceil(prev_value + (prev_value**0.5)*random.gauss(0,1) - 0.5), math.floor(self.initialDemand*0.3))

    def getGraphContext(self):
        ' Should only be run immediately after adding the node into the supplyChain. '
        self.participants = {self.currentTime: (self.supplyChain).predecessors(self)}
        if self.marketShare[self.currentTime] == dict():
            for node in self.participants[self.currentTime]:
                # Note the 'product' portion of the key tuple is redundant
                self.marketShare[self.currentTime][(node,self.product)] = 1.0
        for downstreamNode in self.downstream:
            self.ordersMade[self.currentTime][(downstreamNode ,self.product)] = 0
            self.ordersMade[self.simulationLength][(downstreamNode, self.product)] = 0
            self.downstreamOutstanding[self.currentTime][(downstreamNode,self.product)] = 0
            self.shipmentsReceived[self.currentTime][( downstreamNode,self.product)] = 0
            self.shipmentsReceived[self.simulationLength][(downstreamNode,self.product)] = 0
        # Create node aggregates.
        self.ordersMade[self.currentTime][( 'allNodes', self.product)] = 0
        self.downstreamOutstanding[self.currentTime][( 'allNodes', self.product)] = 0
        self.shipmentsReceived[self.currentTime][('allNodes', self.product)] = 0
        self.ordersMade[self.simulationLength][('allNodes', self.product)] = 0
        self.shipmentsReceived[self.simulationLength][('allNodes', self.product)] = 0
    

    # Query the graph for the node's neighbours            
    def getNeighbours(self):
        self.upstream = (self.supplyChain).successors(self)
        self.downstream = (self.supplyChain).predecessors(self)
    
    
    # Make an order to a downstream node
    def makeOrder(self,targetNode,quantity,product):
        threshold = targetNode.minOrder[product]
        if quantity < 0:
            raise Exception('Negative quantity!: ' + str(quantity))
        if quantity > threshold:
            prevValue = self.ordersMade[self.currentTime].get((targetNode,product),0)
            self.ordersMade[self.currentTime][(targetNode,product)] = prevValue + quantity
            updateAggregatesTemporal(self,self.ordersMade,self.currentTime,targetNode,product,quantity)
            previousValue = findPrevValueRecur(self.downstreamOutstanding, targetNode, product, self.currentTime)[0]
            try:
                self.downstreamOutstanding[self.currentTime][(targetNode,product)] = previousValue + quantity
            except TypeError:
                #print('Probably a None value from findPrevValueRecur. Converting to zero!')
                previousValue = noneToZero(previousValue)
                self.downstreamOutstanding[self.currentTime][(targetNode,product)] = previousValue + quantity
            updateAggregatesPersistent(self,self.downstreamOutstanding,self.currentTime,targetNode,product,quantity)
            proportionFilled = targetNode.makeSale(self,product,quantity)
            self.marketShare[self.currentTime][(targetNode,product)] += proportionFilled
        else:
            pass
            #print('Node ' + self.name + ' attempted to order fewer than the minimum order for ' + targetNode.name  + ' in product ' + product.name  + '.')

    def receiveOrder(self, originNode, quantity, product):
        pass
        #print('Warning, ' + originNode.name + ' tried to make an order to the market ' + self.name + '.')

    # Receive and store product
    def receiveShipment(self,originNode,timeWhenShipped,quantity,product):
        previouslyOutstanding = noneToZero(findPrevValueRecur(self.downstreamOutstanding, originNode, product, self.currentTime)[0])
        self.downstreamOutstanding[self.currentTime][(originNode,product)] = previouslyOutstanding - quantity
        updateAggregatesPersistent(self,self.downstreamOutstanding,self.currentTime,originNode,product,-quantity)
        self.shipmentsReceived[self.currentTime][(originNode,product)] = quantity
        updateAggregatesTemporal(self,self.shipmentsReceived,self.currentTime,originNode,product,quantity)
        self.supplyChain.add_edge(originNode, self, {(timeWhenShipped,originNode,self):(-self.simulationLength,quantity,product)})
    
    # Check for shipments that have arrived
    def checkForShipments(self):
        ' Looks at all incoming edges and checks for any shipments that have \
        spent the requisite time on the edge to arrive'
        for downstreamNode in self.downstream:
            edata = self.supplyChain[downstreamNode][self]
            if isinstance(edata,dict):
                timeToTraverse = edata['timeToTraverse']
                for key in edata:
                    if isinstance(key,tuple):
                        if edata[key] is None:
                            continue
                        if edata[key][0] >= timeToTraverse:
                            currData = edata[key]
                            try:
                                quant, prod = currData[1:3]
                            except:
                                #print currData
                                raise
                            timeWhenShipped = key[0]
                            originNode = key[1]
                            if key[2] == self:
                                self.receiveShipment(originNode,timeWhenShipped, quant, prod)
                            # An 'else' clause here could deal with routing shipments to other nodes!
                            
    def makeAllOrders(self):
        self.marketShare[self.currentTime] = self.marketShare[self.currentTime -1].copy() # This is creating a pointer. FIX ME
        self.marketDemand[self.currentTime] = self.getMarketDemand(self.marketDemand[self.currentTime-1])
        totalReputation = 0
        for entry in self.marketShare[self.currentTime -1]:
            if isinstance(entry,tuple):
                if not isinstance(entry[0], str):
                    totalReputation += self.marketShare[self.currentTime -1][entry]
        for node in self.downstream:
            prevShare, lastUpdateTime = findPrevValueRecur(self.marketShare,node,self.product,self.currentTime-1)
            prevShare = noneToZero(prevShare)
            self.marketShare[self.currentTime][(node,self.product)] = prevShare*(0.9**(self.currentTime-lastUpdateTime))
            try:
                nodeShare = float(prevShare)/(float(totalReputation))
            except ZeroDivisionError:
                #print "Zero divison error in calculating market share for node %r" % (node)
                nodeShare = 1.0/float(len(self.downstream))
            quantity = round(nodeShare*self.marketDemand[self.currentTime],0)
            self.makeOrder(node,quantity,self.product)     
    
    def calculateHealth(self):
        try:
            self.health = self.shipmentsReceived[-1].get(('allNodes','allProducts'),0)/self.ordersMade[-1].get(('allNodes','allProducts'),0)
        except ZeroDivisionError:
            self.health = 1
        return self.health
    
    def getHealth(self):
        return self.health
    
    def makeTimeStep(self):
        self.currentTime += 1
        self.checkForShipments()
        self.makeAllOrders()
        self.health = self.calculateHealth()

    
    

# Commodity market object
class supplyChainCommodityMarket(object):
    #def __init__(self,*args,**kwargs):
    #    self.name = str(args[0]) # (str) human readable name for the object
    #    self.supplyChain = args[1] # (supplyChainNetwork)
    #    assert isinstance(self.supplyChain, supplyChainNetwork)
    #    self.productList = args[2]
    #    self.product = self.productList[0]
    #    # Process optional arguments
    #    self.currentTime = kwargs.get('currentTime',0) # (int) Time at which to initialize node, defaults to 0.
    #    self.minOrder = {prod: (kwargs.get('minOrder',dict())).get(prod, 0) for prod in productList} # (dict) Minimum order accepted, keyed by product. Defaults to 0.
    #    self.inventory = [dict() for x in range(self.simulationLength)] # Inventory array (by time) of dicts (each keyed by product)
    #    self.oldestOrder = dict((product, dict()) for product in self.products) # Dict of dicts, first keyed on product, second keyed on node. Stores time of oldest outstanding orders
    #    self.oldestOrderLastCall = -1 # Currently unused, potential optimisation
    #    self.myHash = hash((self.name, self.supplyChain.name)) # To allow use as keys in dictionaries, etc.
    #    self.stockistPreferences = dict((product,dict()) for product in self.products)
    #    
    #    self.depth = None
    
    def __init__(self,label,graph,product,initialSupply,minOrder,initialInventory,customerRelationships=dict(),startTime=0):
        self.name = label
        self.tier = 100
        self.supplyChain = graph
        self.simulationLength = self.supplyChain.simulationLength
        self.currentTime = startTime
        self.productSupply = [0 for __ in range(self.simulationLength)]
        self.productSupply[self.currentTime] = initialSupply
        self.inventory = [0 for __ in range(self.simulationLength)]
        self.inventory[self.currentTime] = initialInventory
        self.product = product
        self.products = [self.product]
        self.resourceSupply = {self.currentTime: initialSupply}
        self.minOrder = minOrder # (int) Minimum order for upstream nodes
        # Initialize some other essentials
        self.inventory = [dict() for x in range(self.simulationLength)] # Inventory array (by time) of dicts (each keyed by product)
        self.oldestOrder = dict((product, dict()) for product in self.products) # Dict of dicts, first keyed on product, second keyed on node. Stores time of oldest outstanding orders
        self.oldestOrderLastCall = -1 # Currently unused, potential optimisation
        # Market reputation probably a better term
        self.customerRelationships = customerRelationships
        self.ordersReceived = dict()
        self.upstreamOutstanding = dict()
        self.shipmentsMade=dict()
        self.upstream = []
        self.downstream = []
        self.totalReputation = [0 for x in range(0,self.simulationLength)]

    def __repr__(self):
        return ("supplyChainCommodityMarket(name=%r,upstreamOutstanding=%r)" % 
            (self.name, self.upstreamOutstanding[self.currentTime][('allNodes','allProducts')]))

    def getGraphContext(self):
        self.participants = {self.currentTime: (self.supplyChain).successors(self)}
        if self.customerRelationships == dict():
            for node in self.participants[self.currentTime]:
                # Note the 'product' portion of the key tuple is redundant
                self.customerRelationships[self.currentTime][(node,self.product)] = 1
                self.totalReputation[self.currentTime] += 1
        for upstreamNode in self.upstream:
            self.ordersReceived[self.currentTime][( upstreamNode ,self.product)] = 0
            self.upstreamOutstanding[self.currentTime][( upstreamNode ,self.product)] = 0
            self.shipmentsMade[self.currentTime][( upstreamNode ,self.product)] = 0
        # Create node aggregates.
        self.ordersReceived[self.currentTime][( 'allNodes', self.product)] = 0
        self.upstreamOutstanding[self.currentTime][( 'allNodes', self.product)] = 0
        self.shipmentsMade[self.currentTime][( 'allNodes', self.product)] = 0

    # Query the graph for the node's neighbours.         
    def getNeighbours(self):
        self.upstream = (self.supplyChain).successors(self)
        self.downstream = (self.supplyChain).predecessors(self)

    def produceMaterials(self):
        newMaterials = self.getMarketDemand(self.productSupply[self.currentTime-1])
        self.inventory[self.currentTime] += newMaterials
    

    # Receive an order from an upstream node.
    def receiveOrder(self,originNode,quantity,product):
        if quantity > self.minOrder[product]:
            self.ordersReceived[self.currentTime][(originNode,product)] = quantity
            updateAggregatesTemporal(self,self.ordersReceived,self.currentTime,originNode,product,quantity)
            previouslyOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding, originNode, product, self.currentTime)[0])
            self.upstreamOutstanding[self.currentTime][(originNode,product)] = previouslyOutstanding + quantity
            updateAggregatesPersistent(self,self.upstreamOutstanding,self.currentTime,originNode,product,quantity)
        else:
            pass
            #print('Node ' + originNode.name + ' attempted to order ' + str(quantity) + ' units of ' + product.name + ', fewer than the minimum order (' +str(self.minOrder[product]) + ') for ' + self.name + '.')
            #print('Order cancelled.')
    
    def updateRelationships(self):
        for node in self.upstream:
            self.customerRelationships[(self.currenTime,node,self.product)]

    
    # Make a shipment to an upstream node.
    def makeShipment(self,targetNode,quantity,product):
        # Make sure sufficient product exists
        assert quantity > 0
        if quantity > self.inventory[self.currentTime][product]:
            pass
            #print 'Attempted to ship more stock than currently available in inventory'
            #print 'Shipment cancelled'
        elif not targetNode in self.supplyChain.successors(self):
            pass
            #print 'Attempted to ship to a node without a valid edge in place'
            #print 'Shipment cancelled'
            #print "N.B. getNeighbours() can be used to update a node's knowledge of its neighbours"
        else:
            # Place the shipment on the edge
            self.supplyChain.add_edge(self, targetNode, {(self.currentTime,self,targetNode):(0,quantity,product)})
            self.inventory[self.currentTime][product] -= quantity
            # Update the outstanding orders
            previouslyOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding, targetNode, product, self.currentTime)[0])
            self.upstreamOutstanding[self.currentTime][(targetNode,product)] = previouslyOutstanding - quantity
            updateAggregatesPersistent(self,self.upstreamOutstanding,self.currentTime,targetNode,product,-quantity)
            self.shipmentsMade[self.currentTime][(targetNode,product)] = quantity
            updateAggregatesTemporal(self,self.shipmentsMade,self.currentTime,targetNode,product,quantity)
    
    # Finds the time period of the oldest outstanding order from /node/
    # returns the outstanding quantity and the period in which it was ordered.
    def findOldestOutstandingOrder(self,node,product,startTime):
        quantity, orderTime = findNextValueRecur(self.ordersReceived, node, product, 0)
        shipment, shipmentTime = findNextValueRecur(self.shipmentsMade, node, product, 0)
        while shipment > 0 and shipmentTime < self.currentTime + 1:
            quantity -= shipment
            if quantity <= 0:
                nextOrder = findNextValueRecur(self.ordersReceived, node, product, orderTime)
                quantity  += nextOrder[0]
                orderTime = nextOrder[1]
            shipment, shipmentTime = findNextValueRecur(self.shipmentsMade, node, product, shipmentTime)
        return (quantity, orderTime)
    
    # Make shipments of /product/ according to order in which orders were placed.
    def makeAllProductShipments(self,product):
        totalOutstanding = noneToZero(findPrevValueRecur(self.upstreamOutstanding,'allNodes',product,self.currentTime)[0])
        # Check there are some orders to fulfil!
        if totalOutstanding == 0:
            return True
        # Check there is any stock to fill orders with
        if self.inventory[self.currentTime][product] == 0:
            return True
        # If we have enough product to fulfill all orders, do so
        currInventory = self.inventory[self.currentTime].get(product,0)
        if currInventory >= totalOutstanding:
            for node in self.upstream:
                currOutstanding = findPrevValueRecur(self.upstreamOutstanding,node,product,self.currentTime)[0]
                if currOutstanding > 0:
                    self.makeShipment(node, currOutstanding, product)
            return True 
        # Otherwise, fulfil those orders you can starting with the oldest.
        else:
            # Keep going until no more outstanding orders or no more inventory
            while self.inventory[self.currentTime][product] > 0 and totalOutstanding > 0:
                # Only bother with the complicated stuff if there's more than one upstream neighbour
                if len(self.upstream)>1:
                    # Go through all nodes to find who should get priority
                    for node in self.upstream:
                        currOutstanding = findPrevValueRecur(self.upstreamOutstanding,node,product,self.currentTime)[0]
                        if currOutstanding > 0:
                            oldestOrders = self.oldestOrder[product]
                            oldestOrders[node] = self.findOldestOutstandingOrder(node, product, 0)
                            self.oldestOrderLastCall = self.currentTime
                            noBest = [0, self.currentTime]
                            candBest = oldestOrders[node]
                            if candBest[1] < oldestOrders.get('allNodes',noBest)[1]:
                                oldestOrders['allNodes'] = candBest
                                nextNode = node
                            elif (candBest[1] == oldestOrders.get('allNodes',noBest)[1]
                                and candBest[0] >= oldestOrders.get('allNodes',noBest)[0]):
                                oldestOrders['allNodes'] = candBest
                                nextNode = node
                        else:
                            continue
                    # Having found the oldest order, fulfil in totality if possible.
                    outstandingOld = oldestOrders.get('allNodes',[0])[0]
                    if outstandingOld < 1:
                        return False # Something strange
                    shipmentSize = min(currInventory, outstandingOld)
                    self.makeShipment(nextNode, shipmentSize, product)
                    #print(self.name + ' shipped ' + str(shipmentSize) + ' units of ' + product.name + 'to ' + nextNode.name +'.')
                else:
                    prodRemaining = self.inventory[self.currentTime][product]
                    self.makeShipment(self.upstream[0],prodRemaining,product)
                    #print(self.name + ' shipped ' + str(prodRemaining) + ' units of ' + product.name + ' to its sole upstream neighbour, ' + self.upstream[0].name +'.')
            return True

    # Make shipments of all products
    def makeAllShipments(self):
        for product in self.products:
            self.makeAllProductShipments(product)
    
    # Copy over inventory info
    def updateInventory(self):
        previousInventory = self.inventory[self.currentTime-1]
        for product, quantity in previousInventory.iteritems():
            self.inventory[self.currentTime][product] = quantity
        self.produceMaterials()
    
    def makeTimeStep(self):
        self.currentTime += 1        
        self.updateInvetory()
        self.makeAllShipments()
    

def moveShipments(supplyChain):
    for node1, node2 in supplyChain.edges():
        edata = supplyChain[node1][node2]
        if isinstance(edata,dict):
            for key in edata:
                if isinstance(key,tuple):
                    if edata[key] is None:
                        continue
                    travelTime, quant, prod = edata[key]
                    edata[key]  = (travelTime + 1, quant, prod)
            for key, val in edata.items():
                if val == None:
                    del supplyChain[node1][node2][key]



def makeTimeStep(supplyChain):
    nodeList = supplyChain.orderedNodes()
    moveShipments(supplyChain)
    #print '------------------------------------------'
    for node in nodeList:
        #print ''
        ## Ensure the node has been initialised properly.
        #if node.currentTime == 0:
        #    node.getGraphContext()
        #print node.name + ':'
        #print
        node.makeTimeStep()
    #print '------------------------------------------'

def createSupplyChainObject(nodeAttribDict, supplyChain):
    "Class factory to create the various supply chain actors from attribute dictionaries."
    nodeClasses = {
        'retail market': supplyChainRetailMarket,
        'commodity market': supplyChainCommodityMarket,
        'supply chain': supplyChainNode
        }
    nodeClassAttributes = {
        'retail market': ['label','product','initialDemand','rngSeed'],
        'commodity market': ['label','product','initialSupply',
                             'minOrder','initialInventory'],
        'supply chain': ['label','targetInventory','storageCapacity']
    }
    nodeClass = nodeClasses[nodeAttribDict['nodeRole'].lower()]
    compulsoryArgs = nodeClassAttributes.get(nodeAttribDict.get('nodeRole',None).lower(),None)
    if not nodeClass:
        raise Exception("Node attribute dictionary must include a valid nodeRole. \
                        Valid 'nodeRole's are: 'Retail Market', 'Supply Chain', 'Commodity Market' ")
    else:
        optionalArgs = dict()
        args = []
        for i in range(len(compulsoryArgs)+1):
            if i > 1:
                try:
                    args.append(nodeAttribDict[compulsoryArgs[i-1]])
                    #del nodeAttribDict[compulsoryArgs[i-1]]
                except KeyError:
                    errorMsg = 'Node attribute dictionary has no value for \
                           compulsory argument ' + compulsoryArgs[i-1] + '.'
                    #print errorMsg
                    raise
                
            elif i == 0:
                try:
                    args.append(nodeAttribDict[compulsoryArgs[i]])
                    #del nodeAttribDict[compulsoryArgs[i]]
                except KeyError:
                    errorMsg = 'Node attribute dictionary has no value for \
                           compulsory argument ' + compulsoryArgs[i] + '.'
                    print errorMsg
                    raise
            elif i == 1:
                args.append(supplyChain)
            
        for key, value in nodeAttribDict.iteritems():
            if not key in compulsoryArgs:
                optionalArgs[key] = value
    return nodeClass(*args, **optionalArgs)

def decayInt(ratio):
    r = random.random()
    decrement = 0.5
    r -= decrement
    output = 0
    while r > 0:
        decrement *= ratio
        r -= decrement
        output += 1
    return output

def getBaseProduct(nodeData,finishedProduct,productObjects):
    ''' Returns a supply chain product that should be ordered by upstream nodes '''
    product = nodeData.get('product')
    if nodeData.get('tier') == 0:
        product = finishedProduct
    if not product:
        if nodeData.get('activity','').lower() in ['distribution hub', 'airport']:
            product = finishedProduct
        else:
            product = nodeData.get('activity')
    if isinstance(product, supplyChainProduct):
        productObjects[product.name] = product
    else:
        productObjects[product] = supplyChainProduct(product)
        product = productObjects[product]
    return product

def getComponentProducts(nodeName,nodeData,productObjects,G):
    ''' Returns a dictionary of products from downstream nodes
    along with (randomised) integers which represent the quantity
    used in the recipe for building the node's base product '''
    if nodeData.get('dsProducts') is None:
        dsProducts = dict()
    else:
        dsProducts = nodeData.get('dsProducts')
    downstreamNodes = G.predecessors(nodeName)
    for dsNode in downstreamNodes:
        # Look at the product output by the node
        prodName = G.node[dsNode]['activity']
        lowerName = prodName.lower()
        # See if said product already has a supplyChainProduct associated with it
        if not (lowerName == 'distribution hub' or lowerName == 'airport'):
            prodObj = productObjects.get(prodName)
            # If not, make one.
            if not prodObj:
                productObjects[prodName] = supplyChainProduct(prodName)
            # If we've not already encountered this product at another dsNode
            if not dsProducts.get(productObjects[prodName]):
                # Add it to dsProducts dict with a value somewhere between 1 (likely) and 6 (extremely unlikely)
                dsProducts[productObjects[prodName]] = dsProducts.get(prodName,1) + decayInt(0.52)
            # Otherwise
            else:
                # Increment the value by some integer between 0 (likely) and 5 (extremely unlikely)
                dsProducts[productObjects[prodName]] += decayInt(0.52)
    return dsProducts
    
def getBuildInstructions(nodeData,baseProduct,componentProducts):
    buildInstructions = nodeData.get('buildInstructions')
    if buildInstructions is None:
        buildInstructions = {baseProduct: dict()}
    for component, quantity in componentProducts.iteritems():
        if not component == baseProduct:
            buildInstructions[baseProduct][component] = quantity 
    return buildInstructions


def getNodeRole(nodeName,G):
        ''' Returns a string describing the role of the node in the supply chain'''
        if len(G.successors(nodeName)) == 0:
                return 'retail market'
        else:
                return 'supply chain'

def getImpliedDemand(graph,myNode,dataDict):
    impliedDemand = 0
    for usNode in graph.successors(myNode):
            usNodeData = dataDict[usNode]
            if usNodeData['nodeRole'] ==  'retail market':
                impliedDemand += int(2*math.floor(usNodeData['initialDemand']/len(graph.predecessors(usNode))))
            elif usNodeData['nodeRole'] == 'supply chain':
                target = usNodeData.get('targetInventory',getImpliedDemand(graph,usNode,dataDict))
                if type(target) is dict:
                    target = target[dataDict[myNode]['product']]
                impliedDemand += int(target/len(graph.successors(usNode)))
    return impliedDemand

def getInitialDemand(minDemand):
    return minDemand + decayInt(0.501)*100 + decayInt(0.501)*50 + decayInt(0.501)*10

def generic2Supply(nxGraph,name,simLength,finishedProduct):
    # Create the supplyChainNetwork object
    scNetwork = supplyChainNetwork(name,simulationLength=simLength)
    # Make a copy of the old graph's data
    originalNodes = nxGraph.nodes(data=True)
    newNodes = []
    newNodesDict = dict()
    nodeMap = dict()
    # Sort the nodes so the list starts with the raw materials
    originalNodes = sorted(originalNodes, key=lambda x: x[1]['depth'], reverse=True)
    originalNodes = sorted(originalNodes, key=lambda x: x[1]['tier'], reverse=True)
    # Create the scNetwork product dictionary
    productObjects = {finishedProduct.name : finishedProduct}
    for nodeName, originalData in originalNodes:
        newData = dict()
        newData.update(originalData)
        # Get the node role
        newData['nodeRole'] = getNodeRole(nodeName, nxGraph)
        newData['product'] = getBaseProduct(newData,finishedProduct,productObjects)
        if newData.get('tier') >= 0:
            newData['dsProducts'] = getComponentProducts(nodeName,originalData,productObjects,nxGraph)
            newData['buildInstructions'] = getBuildInstructions(newData,newData['product'],newData.get('dsProducts',dict()))
        newNodes.append(newData)
        newNodesDict[newData['label']] = newData
    newNodes = sorted(newNodes, key=itemgetter('tier'))
    newNodes = sorted(newNodes, key=itemgetter('depth'))
    for nodeData in newNodes:
        targetInven = nodeData.get('targetInventory')
        if nodeData['nodeRole'] == 'retail market':
            nodeData['initialDemand'] = getInitialDemand(50)
            nodeData['rngSeed'] = 999
        else:
            if targetInven is None:
                targetInven = {nodeData['product'] : 0}
            impliedDemand = getImpliedDemand(nxGraph,nodeData['label'],newNodesDict)
            targetInven[nodeData['product']] = impliedDemand
            for component, quantity in nodeData.get('dsProducts',dict()).iteritems():
                targetInven[component] = int(0.5*quantity*targetInven[nodeData['product']])
            for complexProduct in nodeData.get('buildInstructions',dict()):
                nodeData['processingCapacity'] = {nodeData['product'] : int(0.25*targetInven[nodeData['product']])}
            nodeData['targetInventory'] = targetInven
            nodeData['storageCapacity'] = len(nodeData['targetInventory'])*nodeData['targetInventory'][nodeData['product']]
        nodeInstance = createSupplyChainObject(nodeData, scNetwork)
        if nodeInstance == None:
            pass
        scNetwork.add_node(nodeInstance)
        nodeMap[nodeData['label']] = nodeInstance
    for n1, n2, edata in nxGraph.edges(data=True):
        dist = edata.get('distance')
        if dist:
            edata.update({'timeToTraverse':math.ceil(dist/800000.0)})
        else:
            edata.update({'timeToTraverse':1 + 10*decayInt(0.6) + decayInt(0.501)})
        scNetwork.add_edge(nodeMap[n1],nodeMap[n2],attr_dict=edata)
    return scNetwork
    

def exportAsGeneric(scNetwork, oldGraph=None, filename=None):
    if oldGraph is None:
        G = nx.DiGraph()
    else:
        G = oldGraph
    # Loop through the graph, starting with the retail nodes.
    for node in scNetwork.orderedNodes():
        newData = dict()
        t = node.currentTime
        newData['time'] = t
        if isinstance(node, supplyChainNode):
            if len(node.buildInstructions) > 0:
                outputProds = [prod for prod in node.buildInstructions]
                newData['product'] = outputProds[0].name
            elif len(node.inventory[t]) == 1:
                newData['product'] = node.products[0].name
            myInven = node.inventory[t]
            mySimpleInven = dict()
            prodHealthVals = []
            for prod, quant in myInven.iteritems():
                mySimpleInven[prod.name] = quant
                prodHealthVals.append(quant/max(node.targetInventory[prod],1))
            newData['currInventory'] = mySimpleInven
            if hasattr(node, 'salesLost'):
                newData['salesLost'] = node.salesLost[node.simulationLength].get(('allNodes','allProducts'),0)
            dSum = 0
            for prodHealth in prodHealthVals:
                dSum += abs(1-prodHealth)
            newData['health'] = node.health
        elif isinstance(node, supplyChainRetailMarket):
            newData['health'] = node.health
        G.add_node(node.name, newData)
        if len(node.upstream) > 0: 
            for usNode in node.upstream:
                if usNode is None:
                    pass
                edgeData = dict()
                edge_attr_dict = scNetwork.get_edge_data(node,usNode)
                for key, value in edge_attr_dict.iteritems():
                    if type(key) is tuple:
                        newKey = key[0]
                        newVal = {'timeOnEdge': edge_attr_dict[key][0], 'quantity' : edge_attr_dict[key][1], 'product': edge_attr_dict[key][2].name}
                        valString = ', '.join(newVal)
                        edgeData[newKey] = newVal
                if node.label is None or usNode.label is None:
                        continue
                G.add_edge(node.label,usNode.label,attr_dict=edgeData)
    if not filename is None:
        nx.write_gexf(G, filename)
    return G

def getGexf(filename,simLength):
    G = nx.read_gexf(filename)
    new = generic2Supply(G,filename,simLength)
    return new

def calculateDepth(G):
    ''' Add depth attribute to all nodes in networkX graph G'''
    
    def setNodeDepth(G,theNode):
        ''' Recursively calculate the depth of a particular node '''
        if len(G.successors(theNode)) == 0:
            G.node[theNode]['depth'] = 0
        else:
            minDepth = 0
            for usNode in G.successors(theNode):
                usNodeDepth = G.node[usNode].get('depth',setNodeDepth(G,usNode))
                if usNodeDepth < minDepth:
                    minDepth = usNodeDepth
            G.node[theNode]['depth'] = minDepth + 1

    nodeList = []
    for thisNode in G.nodes():
        nodeList.append(G.node[thisNode])
        nodeList[-1]['label'] = thisNode
    nodeList = sorted(nodeList, key=itemgetter('tier'))
    for myNode in nodeList:
        setNodeDepth(G,myNode['label'])   
    

def runSimulation(G,timesteps,randSeed,networkName=None,initOutFile=None,finOutFile=None):
    if type(G) == str:
        G = nx.read_gexf(G)
    if networkName is None:
        networkName = 'supplyChain' + datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
    calculateDepth(G)
    random.seed(randSeed)
    simLength = timesteps + 1
    laptop = supplyChainProduct('laptop')
    scNetwork = generic2Supply(G,networkName,simLength, laptop)
    scNetwork.giveNodeContext()
    if not initOutFile is None:
        exportAsGeneric(scNetwork,G,initOutFile)
    for i in range(timesteps):
        scNetwork.makeTimeStep()
    networkHealth = scNetwork.health
    return exportAsGeneric(scNetwork,G,finOutFile), networkHealth 
