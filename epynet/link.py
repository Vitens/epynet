""" EPYNET Classes """
import math

import epanet2 as ep
from tools import IndexIdType

class Link(object):
    """ EPANET Link Class """
    def __init__(self, index):
        self.index = index

        # lazy variables
        self.uid = ep.ENgetlinkid(index)
        self._lazy_properties = {}

        self.from_node = None
        self.to_node = None

    def __str__(self):
        return self.uid

    def get_property(self, code):
        return ep.ENgetlinkvalue(self.index, code)

    def lazy_get_property(self, code):
        if code not in self._lazy_properties.keys():
            self._lazy_properties[code] = self.get_property(code)
        return self._lazy_properties[code]
    # lazy properties
    @property
    def diameter(self):
        return self.lazy_get_property(0)
    # computed values
    @property
    def flow(self):
        return self.get_property(8)
    @property
    def headloss(self):
        return self.get_property(10)
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
    def roughness(self):
        return self.lazy_get_property(2)
    @property
    def minorloss(self):
        return self.lazy_get_property(3)
    @property
    def status(self):
        return self.get_property(11)

class Pump(Link):
    """ EPANET Pump Class """
    link_type = 'pump'

    @property
    def velocity(self):
        return 1.0

    @property
    def speed(self):
        return self.get_property(5)

    def set_speed(self,speed):
        ep.ENsetlinkvalue(self.index, 5, speed)

class Valve(Link):
    """ EPANET Valve Class """
    link_type = 'valve'

    types = {3:"PRV", 4:"PSV", 5:"PBV", 6:"FCV", 7:"TCV", 8:"GPV"}

    @property
    def setting(self):
        return ep.ENgetlinkvalue(self.index, 5)

    @property
    def valve_type(self):
        type_code = ep.ENgetlinktype(self.index)
        return self.types[type_code]
    def set_setting(self, setting):
        ep.ENsetlinkvalue(self.index, 5, setting)
