""" EPYNET Classes """
import math

from . import epanet2 as ep
from .objectcollection import ObjectCollection
from .node import *
from .link import * 
from .curve import *
from .pattern import *

class Network(object):
    """ EPANET Network Simulation Class """
    def __init__(self, inputfile = None, units = ep.EN_CMH, headloss = ep.EN_DW):

        self.ep = ep
        if inputfile:
            self.inputfile = inputfile
            self.rptfile = self.inputfile[:-3]+"rpt"
            self.binfile = self.inputfile[:-3]+"bin"
            ep.ENopen(self.inputfile, self.rptfile, self.binfile)
        else:
            self.rptfile = "net.rpt"
            self.binfile = "net.bin"
            ep.ENinit(self.rptfile.encode(), self.binfile.encode(), units, headloss)

        # prepare network data
        self.nodes = ObjectCollection()
        self.junctions = ObjectCollection()
        self.reservoirs = ObjectCollection()
        self.tanks = ObjectCollection()

        self.links = ObjectCollection()
        self.pipes = ObjectCollection()
        self.valves = ObjectCollection()
        self.pumps = ObjectCollection()

        self.curves = ObjectCollection()
        self.patterns = ObjectCollection()

        self.solved = False

        self.load_network()

    def load_network(self):
        """ Load network data """
        # load nodes
        for index in range(1, ep.ENgetcount(ep.EN_NODECOUNT)+1):
            # get node type
            node_type =ep.ENgetnodetype(index)
            uid = ep.ENgetnodeid(index)

            if node_type == 0:
                node = Junction(uid)
                self.junctions[node.uid] = node
            elif node_type == 1:
                node = Reservoir(uid)
                self.reservoirs[node.uid] = node
                self.nodes[node.uid] = node
            else:
                node = Tank(uid)
                self.tanks[node.uid] = node

            self.nodes[node.uid] = node

        # load links
        for index in range(1, ep.ENgetcount(ep.EN_LINKCOUNT)+1):
            link_type = ep.ENgetlinktype(index)
            uid = ep.ENgetlinkid(index)
            # pipes
            if link_type <= 1:
                link = Pipe(uid)
                self.pipes[link.uid] = link
            elif link_type == 2:
                link = Pump(uid)
                self.pumps[link.uid] = link
            elif link_type >= 3:
                link = Valve(uid)
                self.valves[link.uid] = link

            self.links[link.uid] = link
            link_nodes = ep.ENgetlinknodes(index)
            link.from_node = self.nodes[ep.ENgetnodeid(link_nodes[0])]
            link.from_node.links[link.uid] = link
            link.to_node = self.nodes[ep.ENgetnodeid(link_nodes[1])]
            link.to_node.links[link.uid] = link

        # load curves
        for index in range(1, ep.ENgetcount(ep.EN_CURVECOUNT)+1):
            uid = ep.ENgetcurveid(index)
            self.curves[uid] = Curve(uid)
        # load patterns
        for index in range(1, ep.ENgetcount(ep.EN_PATCOUNT)+1):
            uid = ep.ENgetpatternid(index)
            self.patterns[uid] = Pattern(uid)

    def reset(self):

        self.solved = False

        for link in self.links:
            link.reset()
        for node in self.nodes:
            node.reset()

    def delete_node(self, uid):
        index = ep.ENgetnodeindex(uid)
        node_type = ep.ENgetnodetype(index)

        for link in list(self.nodes[uid].links):
            self.delete_link(link.uid);

        del self.nodes[uid]

        if node_type == ep.EN_JUNCTION:
            del self.junctions[uid]
        elif node_type == ep.EN_RESERVOIR:
            del self.reservoirs[uid]
        elif node_type == ep.EN_TANK:
            del self.tanks[uid]

        ep.ENdeletenode(index)

    def delete_link(self, uid):

        index = ep.ENgetlinkindex(uid)
        link_type = ep.ENgetlinktype(index)

        link = self.links[uid]
        del link.from_node.links[uid]
        del link.to_node.links[uid]

        del self.links[uid]

        if link_type == ep.EN_PIPE or link_type == ep.EN_CVPIPE:
            del self.pipes[uid]
        elif link_type == ep.EN_RESERVOIR:
            del self.pumps[uid]
        else:
            del self.valves[uid]

        ep.ENdeletelink(index)

    def add_reservoir(self, uid, x, y, elevation=0):
        ep.ENaddnode(uid, ep.EN_RESERVOIR)
        index = ep.ENgetnodeindex(uid)
        ep.ENsetcoord(index, x, y)
        node = Reservoir(uid)
        self.reservoirs[uid] = node
        self.nodes[uid] = node

        return node

    def add_junction(self, uid, x, y, basedemand=0, elevation=0):
        ep.ENaddnode(uid, ep.EN_JUNCTION)
        index = ep.ENgetnodeindex(uid)
        ep.ENsetcoord(index, x, y)
        node = Junction(uid)
        self.junctions[uid] = node
        self.nodes[uid] = node

        # configure node
        node.basedemand = basedemand
        node.elevation = elevation

        return node

    def add_tank(self, uid, x, y, diameter=0, maxlevel=0, minlevel=0, tanklevel=0):
        ep.ENaddnode(uid, ep.EN_TANK)
        index = ep.ENgetnodeindex(uid)
        ep.ENsetcoord(index, x, y)
        node = Tank(uid)
        self.tanks[uid] = node
        self.nodes[uid] = node
        # config tank
        node.diameter = diameter
        node.maxlevel = maxlevel
        node.minlevel = minlevel
        node.tanklevel = tanklevel
        return node


    def add_pipe(self, uid, from_node, to_node, diameter=100, length=10, roughness=0.1, check_valve=False):

        from_node = from_node if isinstance(from_node,str) else from_node.uid
        to_node = to_node if isinstance(to_node,str) else to_node.uid

        if check_valve:
            ep.ENaddlink(uid, ep.EN_CVPIPE, from_node, to_node)
        else:
            ep.ENaddlink(uid, ep.EN_PIPE, from_node, to_node)

        index = ep.ENgetlinkindex(uid)
        link = Pipe(uid)

        link.diameter = diameter
        link.length = length
        link. roughness = roughness

        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pipes[uid] = link
        self.links[uid] = link

        # set link properties
        link.diameter = diameter
        link.length = length

        return link

    def add_pump(self, uid, from_node, to_node, speed=0):

        from_node = from_node if isinstance(from_node,str) else from_node.uid
        to_node = to_node if isinstance(to_node,str) else to_node.uid

        ep.ENaddlink(uid, ep.EN_PUMP, from_node, to_node)
        index = ep.ENgetlinkindex(uid)
        link = Pump(uid)
        link.speed = speed
        link.from_node = self.nodes[from_node]
        link.speed = speed
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.pumps[uid] = link
        self.links[uid] = link

        return link

    def add_curve(self, uid, values):
        ep.ENaddcurve(uid)

        curve = Curve(uid)
        curve.values = values
        self.curves[uid] = curve

        return curve

    def add_pattern(self, uid, values):
        ep.ENaddpattern(uid)
        pattern = Pattern(uid)
        pattern.values = values
        self.patterns[uid] = pattern

        return pattern

    def add_valve(self, uid, valve_type, from_node, to_node, diameter=100, setting=0):

        from_node = from_node if isinstance(from_node,str) else from_node.uid
        to_node = to_node if isinstance(to_node,str) else to_node.uid

        if valve_type.lower() == "gpv":
            valve_type_code = ep.EN_GPV
        elif valve_type.lower() == "fcv":
            valve_type_code = ep.EN_FCV
        elif valve_type.lower() == "pbv":
            valve_type_code = ep.EN_PBV
        elif valve_type.lower() == "tcv":
            valve_type_code = ep.EN_TCV
        elif valve_type == "prv":
            valve_type_code = ep.EN_PRV
        else:
            raise InputError("Unknown Valve Type")

        ep.ENaddlink(uid, valve_type_code, from_node, to_node)
        index = ep.ENgetlinkindex(uid)
        link = Valve(uid)
        link.diameter = diameter
        link.setting = setting
        link.from_node = self.nodes[from_node]
        link.to_node = self.nodes[to_node]
        link.to_node.links[link.uid] = link
        link.from_node.links[link.uid] = link
        self.valves[uid] = link
        self.links[uid] = link

        return link

    def get_warnings(self):
        """ Get EPANET2 GUI style warning messages """
        warnings = []
        if not self.solved:
            raise ValueError('This function only works for single-step solved networks')

        # check fcv
        for valve in self.valves:
            if valve.valve_type == 'FCV' and valve.flow < valve.setting:
                warnings.append("FCV "+valve.uid+" unable to deliver flow")

        return warnings

    def solve(self, simtime=0):
        """ Solve Hydraulic Network for Single Timestep"""
        self.reset()
        ep.ENsettimeparam(4,simtime)
        ep.ENopenH()
        ep.ENinitH(0)
        ep.ENrunH()
        ep.ENcloseH()
        self.solved = True

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

    def save_inputfile(self, name):
        ep.ENsaveinpfile(name)

