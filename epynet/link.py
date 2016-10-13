""" EPYNET Classes """
import math
import pudb
import pandas as pd

import epanet2 as ep
from tools import IndexIdType
from baseobject import BaseObject

class Link(object):
    """ EPANET Link Class """

    static_properties = {}
    properties = {'flow':ep.EN_FLOW}

    def __init__(self, index):
        self.index = index
        # lazy variables
        self.uid = ep.ENgetlinkid(index)
        self._static_values = {}

        self.results = {}
        self.times = []

        self.from_node = None
        self.to_node = None

    def __getattr__(self, name):
        if name in self.static_properties.keys():
            return self.get_static_property(self.static_properties[name])
        elif name in self.properties.keys():
            if self.results == {}:
                return self.get_property(self.properties[name])
            else:
                return pd.Series(self.results[name], index=self.times)
        else:
            raise AttributeError('Nonexistant Attribute',name)

    def __setattr__(self, name, value):
        if name in self.properties.keys():
            raise AttributeError("Illegal Assignment to Computed Value")
        if name in self.static_properties.keys():
            self.set_static_property(self.static_properties[name],value)
        else:
            super(Link, self).__setattr__(name, value)

    def __str__(self):
        return self.uid

    def set_static_property(self, code, value):
        self._static_values[code] = value
        ep.ENsetlinkvalue(self.index, code, value) 

    def get_property(self, code):
        return ep.ENgetlinkvalue(self.index, code)

    def get_static_property(self, code):
        if code not in self._static_values.keys():
            self._static_values[code] = self.get_property(code)
        return self._static_values[code]

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

    static_properties = {'diameter':ep.EN_DIAMETER, 'length':ep.EN_LENGTH,
                         'roughness':ep.EN_ROUGHNESS, 'minorloss':ep.EN_MINORLOSS,
                          'status':ep.EN_STATUS}
    properties = {'flow':ep.EN_FLOW, 'headloss':ep.EN_HEADLOSS, 'velocity':ep.EN_VELOCITY}

class Pump(Link):
    """ EPANET Pump Class """
    link_type = 'pump'

    static_properties = {'length':ep.EN_LENGTH, 'speed':ep.EN_INITSETTING}
    properties = {'flow':ep.EN_FLOW}

    @property
    def velocity(self):
        return 1.0

class Valve(Link):
    """ EPANET Valve Class """

    static_properties = {'setting':ep.EN_INITSETTING}

    link_type = 'valve'

    types = {3:"PRV", 4:"PSV", 5:"PBV", 6:"FCV", 7:"TCV", 8:"GPV"}

    @property
    def valve_type(self):
        type_code = ep.ENgetlinktype(self.index)
        return self.types[type_code]
