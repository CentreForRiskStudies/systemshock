__author__ = 'Louise'

# various things to help get parameter files and so on.
# takes csv files and munges them

import csv
import re  # regular expressions
import random

import networkx as nx


def read_lat_long(fname):
    """
    Read lat long info from a csv file.
    Each line of the file should contain a country name, followed by the area name,
    lat long string, and finally the adjacency information
    All this is munged into a graph, which is then written out as a gexf file
    Also, a file is written containing outline bank parameters
    @param fname:
    @return:
    """
    with open(fname, 'rb') as csvFile:
        G = nx.DiGraph()
        cReader = csv.reader(csvFile, delimiter=',')
        areaDict = {}  # holds non-core countries in the area
        for row in cReader:
            country = row[0]
            area = row[1]
            isCore = row[2] == "TRUE"  # convert from string to boolean
            if not area in areaDict:
                areaDict[area] = []
            if not isCore:
                areaDict[area].append(country)
            point = getPointFromString(row[3])
            G.add_node(country, region=area, wkt=point,
                       core=str(isCore))  # note this updates attributes if node already exists
            G.add_edges_from([(other, country) for other in row[4:]])

        # now make non-core countries have up to 3 edges to other countries in the same area
        for country in G:
            isCore = G.node[country]['core']
            if isCore != "True":
                area = G.node[country]['region']
                neighbours = areaDict[area][:]  # take a copy
                neighbours.remove(country)
                nLinks = min(3, len(neighbours))
                G.add_edges_from([country, other] for other in random.sample(neighbours, nLinks))
        nx.write_gexf(G, "countries.gexf")

        # now write out some bits of xml that can be used in a parameters file
        with open("skeleton-countries.xml", 'w') as cFile:
            for area in areaDict.keys():
                xmlString = "\n<economy name=\"%s\">\n</economy>\n" % area
                cFile.write(xmlString)
            for country in G:
                xmlString = ("\n<bank name=\"%s\" economy=\"%s\" location=\"%s\" core=\"%s\">\n</bank>\n" %
                             (country, G.node[country]['region'], G.node[country]['wkt'], G.node[country]['core']))
                cFile.write(xmlString)


def getPointFromString(llStr):
    mStr = r"([0-9]+)d([0-9.]+)m([0-9.]+s)?([NS]) ([0-9]+)d([0-9.]+)m([0-9.]+s)?([EW])"
    matches = re.match(mStr, llStr)
    lat = float(matches.group(1)) + float(matches.group(2)) / 60.0
    if 'S' == matches.group(4):
        lat = - lat
    lng = float(matches.group(5)) + float(matches.group(6)) / 60.0
    if 'W' == matches.group(8):
        lng = -lng
    return "POINT({:f} {:f})".format(lng, lat)


if __name__ == '__main__':
    import sys

    read_lat_long(sys.argv[1])
