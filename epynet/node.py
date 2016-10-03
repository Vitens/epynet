""" EPYNET Classes """
import epanet2 as ep
from tools import IndexIdType

class Node(object):
    """ Base EPANET Node class """
    def __init__(self, index):
        self.index = index

        self.links = []
        self.uid = ep.ENgetnodeid(index)

        self._lazy_properties = {}

    def __str__(self):
        return self.uid

    def get_property(self, code):
        return ep.ENgetnodevalue(self.index, code)

    def lazy_get_property(self, code):
        if code not in self._lazy_properties.keys():
            self._lazy_properties[code] = self.get_property(code)
        return self._lazy_properties[code]

    
    @property
    def coordinates(self):
        if "coords" not in self._lazy_properties.keys():
            self._lazy_properties["coords"] = ep.ENgetcoord(self.index)
        return self._lazy_properties["coords"]

    # lazy properties
    @property
    def elevation(self):
        return self.lazy_get_property(0)
    # computed values
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
        """ calculates all the water flowing out of the node """
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

    @property
    def demand(self):
        return self.get_property(9)
    @property
    def basedemand(self):
        return self.lazy_get_property(1)


class Tank(Node):
    """ EPANET Reservoir Class """
    node_type = "Tank"

    @property
    def initvolume(self):
        return self.lazy_get_property(14)
    @property
    def diameter(self):
        return self.lazy_get_property(17)
    @property
    def minvolume(self):
        return self.lazy_get_property(18)
    @property
    def minlevel(self):
        return self.lazy_get_property(20)
    @property
    def maxlevel(self):
        return self.lazy_get_property(21)
    @property
    def volume(self):
        return self.get_property(24)
    @property
    def maxvolume(self):
        return self.lazy_get_property(25)



