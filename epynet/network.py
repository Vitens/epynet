""" EPYNET Classes """
import math

import epanet2 as ep
from objectcollection import ObjectCollection
from node import *
from link import * 

class Network(object):
    """ EPANET Network Simulation Class """
    def __init__(self, inputfile):
        self.inputfile = inputfile
        self.rptfile = self.inputfile[:-3]+"rpt"
        self.binfile = self.inputfile[:-3]+"bin"

        ep.ENopen(self.inputfile, self.rptfile, self.binfile)

        # prepare network data
        self.nodes = ObjectCollection()
        self.junctions = ObjectCollection()
        self.reservoirs = ObjectCollection()
        self.tanks = ObjectCollection()

        self.links = ObjectCollection()
        self.pipes = ObjectCollection()
        self.valves = ObjectCollection()
        self.pumps = ObjectCollection()

        self.load_network()

    def load_network(self):
        """ Load network data """
        # load nodes
        for index in range(1, ep.ENgetcount(ep.EN_NODECOUNT)+1):
            # get node type
            node_type =ep.ENgetnodetype(index)
            if node_type == 0:
                node = Junction(index)
                self.junctions[node.uid] = node
            elif node_type == 1:
                node = Reservoir(index)
                self.reservoirs[node.uid] = node
                self.nodes[node.uid] = node
            else:
                node = Tank(index)
                self.tanks[node.uid] = node

            self.nodes[node.uid] = node

        # load links
        for index in range(1, ep.ENgetcount(ep.EN_LINKCOUNT)+1):
            link_type = ep.ENgetlinktype(index)
            # pipes
            if link_type <= 1:
                link = Pipe(index)
                self.pipes[link.uid] = link
            elif link_type == 2:
                link = Pump(index)
                self.pumps[link.uid] = link
            elif link_type >= 3:
                link = Valve(index)
                self.valves[link.uid] = link

            self.links[link.uid] = link
            link_nodes = ep.ENgetlinknodes(index)
            link.from_node = self.nodes[Node(link_nodes[0]).uid]
            link.from_node.links[link.uid] = link
            link.to_node = self.nodes[Node(link_nodes[1]).uid]
            link.to_node.links[link.uid] = link

    def reset(self):
        map(lambda obj: obj.reset(), self.links)
        map(lambda obj: obj.reset(), self.nodes)

    def solve(self, simtime=0):
        """ Solve Hydraulic Network for Single Timestep"""
        self.reset()
        ep.ENsettimeparam(4,simtime)
        ep.ENopenH()
        ep.ENinitH(0)
        ep.ENrunH()
        ep.ENcloseH()

    def run(self):
        self.reset()
        self.time = []
        # open network
        ep.ENopenH()
        ep.ENinitH(0)

        simtime = 0
        timestep = 1
        while timestep > 0:
            ep.ENrunH()
            timestep = ep.ENnextH()
            self.time.append(simtime)
            self.load_attributes(simtime)
            simtime += timestep

    def load_attributes(self, simtime):
        for node in self.nodes:
            for property_name in node.properties.keys():
                if property_name not in node.results.keys():
                    node.results[property_name] = []
                node.results[property_name].append(node.get_property(node.properties[property_name]))
            node.times.append(simtime)

        for link in self.links:
            for property_name in link.properties.keys():
                if property_name not in link.results.keys():
                    link.results[property_name] = []
                link.results[property_name].append(link.get_property(link.properties[property_name]))
            link.times.append(simtime)
