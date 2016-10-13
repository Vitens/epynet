""" EPYNET Classes """
import epanet2 as ep
from tools import IndexIdType

class Node(object):
    """ Base EPANET Node class """

    static_properties = {'elevation': ep.EN_ELEVATION}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE}

    def __init__(self, index):
        self.index = index

        self.links = []
        self.results = {}
        self.times = []

        self.uid = ep.ENgetnodeid(index)
        self._static_values = {}

    def __str__(self):
        return self.uid

    def __getattr__(self, name):
        if name in self.static_properties.keys():
            return self.get_static_property(self.static_properties[name])
        elif name in self.properties.keys():
            return self.get_property(self.properties[name])
        else:
            raise AttributeError('Nonexistant Attribute',name)

    def __setattr__(self, name, value):
        if name in self.properties.keys():
            raise AttributeError("Illegal Assignment to Computed Value")
        if name in self.static_properties.keys():
            self.set_static_property(self.static_properties[name],value)
        else:
            super(Node, self).__setattr__(name, value)

    def __str__(self):
        return self.uid

    def set_static_property(self, code, value):
        self._static_values[code] = value
        ep.ENsetnodevalue(self.index, code, value) 

    def get_property(self, code):
        return ep.ENgetnodevalue(self.index, code)

    def get_static_property(self, code):
        if code not in self._static_values.keys():
            self._static_values[code] = self.get_property(code)
        return self._static_values[code]

    
    @property
    def coordinates(self):
        if "coords" not in self._static_values.keys():
            self._static_values["coords"] = ep.ENgetcoord(self.index)
        return self._static_values["coords"]

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
        """ calculates all the water flowing out of the node """
        outflow = 0
        for link in self.downstream_links:
            outflow += abs(link.flow)
        return outflow

class Reservoir(Node):
    """ EPANET Reservoir Class """
    node_type = "Reservoir"

class Junction(Node):
    """ EPANET Junction Class """

    static_properties = {'elevation': ep.EN_ELEVATION, 'basedemand': ep.EN_BASEDEMAND}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE, 'demand': ep.EN_DEMAND}
    node_type = "Junction"


class Tank(Node):
    """ EPANET Tank Class """
    node_type = "Tank"

    static_properties = {'elevation': ep.EN_ELEVATION, 'basedemand': ep.EN_BASEDEMAND,
                         'initvolume': ep.EN_INITVOLUME, 'diameter': ep.EN_TANKDIAM,
                         'minvolume': ep.EN_MINVOLUME, 'minlevel': ep.EN_MINLEVEL,
                         'maxlevel': ep.EN_MAXLEVEL, 'maxvolume': 25}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE, 'demand': ep.EN_DEMAND, 'volume': 24, 'level': ep.EN_TANKLEVEL}
