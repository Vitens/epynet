""" EPYNET Classes """
import math

import epanet2 as ep
from .tools import IndexIdType

def get_epanet_error(error_code):
    """ Raise Exception and get error information if necessary """
    if error_code:
        error_description = ep.ENgeterror(error_code, 500)[1]
        error_string = str(error_code) + " " + error_description
        raise Exception(error_string)

def check(result_list):
    """ Check the returned response from an EPANET2 function
    for errors, and remove the error status from the response."""

    if type(result_list) is not list:
        result = [result_list]
    else:
        result = result_list

    # Check for epanet error
    get_epanet_error(result[0])

    if len(result) == 2:
        return result[1]
    else:
        return result[1:]

class Node(object):
    """ Base EPANET Node class """
    def __init__(self, index, coordinates):
        self.index = index

        self.links = []
        # Lazy variables
        self.uid = check(ep.ENgetnodeid(index))
        self.coordinates = coordinates[self.uid]
        self._lazy_properties = {}

    def __str__(self):
        return self.uid

    def get_property(self, code):
        return check(ep.ENgetnodevalue(self.index, code))

    def lazy_get_property(self, code):
        if code not in self._lazy_properties.keys():
            self._lazy_properties[code] = self.get_property(code)
        return self._lazy_properties[code]

    @property
    def node_id(self):
        return self.uid

    #lazy properties
    @property
    def elevation(self):
        return self.lazy_get_property(0)

    # computed values
    @property
    def demand(self):
        return self.get_property(9)
    @property
    def head(self):
        return self.get_property(10)
    @property
    def pressure(self):
        return self.get_property(11)

    # extra functionality
    @property
    def upstream_links(self):
        """ return a list of upstream links """
        links = []
        for link in self.links:
            if (link.to_node == self and link.flow >= 0) or (link.from_node == self and link.flow < 0):
                links.append(link)
                
        return links

    @property
    def downstream_links(self):
        """ return a list of downstream nodes """
        links = []
        for link in self.links:
            if (link.from_node == self and link.flow >= 0) or (link.to_node == self and link.flow < 0):
                links.append(link)
        return links

    @property
    def inflow(self):
        """ calculates all the water flowing into the node """
        inflow = 0
        for link in self.upstream_links:
            inflow += abs(link.flow)
        return inflow

    @property
    def outflow(self):
        outflow = 0
        for link in self.downstream_links:
            outflow += abs(link.flow)
        return outflow

class Reservoir(Node):
    """ EPANET Reservoir Class """
    node_type = "Reservoir"

class Junction(Node):
    """ EPANET Reservoir Class """
    node_type = "Junction"

class Tank(Node):
    """ EPANET Reservoir Class """
    node_type = "Tank"

class Link(object):
    """ EPANET Link Class """
    def __init__(self, index):
        self.index = index

        # lazy variables
        self.uid = check(ep.ENgetlinkid(index))
        self._lazy_properties = {}

        self.from_node = None
        self.to_node = None
    def __str__(self):
        return self.uid

    def get_property(self, code):
        return check(ep.ENgetlinkvalue(self.index, code))

    def lazy_get_property(self, code):
        if code not in self._lazy_properties.keys():
            self._lazy_properties[code] = self.get_property(code)
        return self._lazy_properties[code]
    # lazy properties
    @property
    def link_id(self):
        return self.uid

    @property
    def diameter(self):
        return self.lazy_get_property(0)
    # computed values
    @property
    def flow(self):
        return self.get_property(8)
    @property
    def velocity(self):
        return self.get_property(9)

    # upstream and downstream nodes
    @property
    def upstream_node(self):
        if self.flow >= 0:
            return self.from_node
        else:
            return self.to_node
    @property
    def downstream_node(self):
        if self.flow >= 0:
            return self.to_node
        else:
            return self.from_node

class Pipe(Link):
    """ EPANET Pipe Class """
    link_type = 'pipe'
    @property
    def length(self):
        return self.lazy_get_property(1)
    @property
    def opened(self):
        return self.get_property(11)
    @property
    def volume(self):
        return self.length * 1/4 * math.pi * self.diameter ** 2

class Pump(Link):
    """ EPANET Pump Class """
    link_type = 'pump'

    @property
    def velocity(self):
        return 1

    def set_speed(self,speed):
        check(ep.ENsetlinkvalue(self.index, 5, speed))

class Valve(Link):
    """ EPANET Valve Class """
    link_type = 'valve'

    types = {3:"PRV", 4:"PSV", 5:"PBV", 6:"FCV", 7:"TCV", 8:"GPV"}

    @property
    def setting(self):
        return check(ep.ENgetlinkvalue(self.index, 5))

    @property
    def valve_type(self):
        type_code = check(ep.ENgetlinktype(self.index))
        return self.types[type_code]
    def set_setting(self, setting):
        check(ep.ENsetlinkvalue(self.index, 5, setting))

class Network(object):
    """ EPANET Network Simulation Class """
    def __init__(self, inputfile):
        self.inputfile = inputfile
        self.rptfile = self.inputfile[:-3]+"rpt"
        self.binfile = self.inputfile[:-3]+"bin"

        ep.ENopen(self.inputfile, self.rptfile, self.binfile)

        self.nodes = IndexIdType()
        self.junctions = IndexIdType()
        self.reservoirs = IndexIdType()
        self.tanks = IndexIdType()
        self.links = IndexIdType()
        self.pipes = IndexIdType()
        self.valves = IndexIdType()
        self.pumps = IndexIdType()

        self.load_network()

    def load_network(self):
        """ Load network data """
        coordinates = self.get_node_coordinates()
        # load nodes
        for index in range(1, check(ep.ENgetcount(ep.EN_NODECOUNT))+1):
            # get node type
            node_type = check(ep.ENgetnodetype(index))
            if node_type == 0:
                junction = Junction(index, coordinates)
                self.junctions[index] = junction
                self.nodes[index] = junction
            elif node_type == 1:
                reservoir = Reservoir(index, coordinates)
                self.reservoirs[index] = reservoir
                self.nodes[index] = reservoir
            else:
                tank = Tank(index, coordinates)
                self.tanks[index] = tank
                self.nodes[index] = tank

        # load links
        for index in range(1, check(ep.ENgetcount(ep.EN_LINKCOUNT))+1):
            link_type = check(ep.ENgetlinktype(index))
            # pipes
            if link_type <= 1:
                link = Pipe(index)
                self.pipes[index] = link
            elif link_type == 2:
                link = Pump(index)
                self.pumps[index] = link
            elif link_type >= 3:
                link = Valve(index)
                self.valves[index] = link

            self.links[index] = link
            link_nodes = check(ep.ENgetlinknodes(index))
            link.from_node = self.nodes[link_nodes[0]]
            link.from_node.links.append(link)
            link.to_node = self.nodes[link_nodes[1]]
            link.to_node.links.append(link)


    def get_node_coordinates(self):
        """ Parse through the input file to extract the node coordinates """
        coordinates = dict()

        handle = open(self.inputfile)
        capture = False
        for line in handle.readlines():
            if "[COORDINATES]" in line:
                capture = True
                continue
            # stop capturing
            if line[0] is "[":
                capture = False

            if capture and line[0] is not ";" and line.strip() is not "":
                split = line.split("\t")
                coordinates[split[0].strip()] = [float(split[1].strip()), float(split[2].strip())]

        return coordinates

    #@staticmethod
    def solve(self, simtime=0):
        """ Solve Hydraulic Network """
        check(ep.ENsettimeparam(4,simtime))
        check(ep.ENopenH())
        check(ep.ENinitH(0))
        check(ep.ENrunH())
        check(ep.ENcloseH())
        #check(ep.ENcloseH())
