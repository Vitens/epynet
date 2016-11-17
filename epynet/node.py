""" EPYNET Classes """
import epanet2 as ep
from objectcollection import ObjectCollection
from baseobject import BaseObject

class Node(BaseObject):
    """ Base EPANET Node class """

    static_properties = {'elevation': ep.EN_ELEVATION}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE}

    def __init__(self, uid):
        super(Node, self).__init__(uid)
        self.links = ObjectCollection()

    def get_index(self, uid):
        return ep.ENgetnodeindex(uid)

    def set_object_value(self, uid, code, value):
        index = self.get_index(uid)
        return ep.ENsetnodevalue(index, code, value)

    def get_object_value(self, uid, code):
        index = self.get_index(uid)
        return ep.ENgetnodevalue(index, code)

    @property
    def index(self):
        return self.get_index(self.uid)

    @property
    def coordinates(self):
        if "coords" not in self._static_values.keys():
            self._static_values["coords"] = ep.ENgetcoord(self.index)
        return self._static_values["coords"]

    # extra functionality
    @property
    def upstream_links(self):
        """ return a list of upstream links """
        if self.results != {}:
            raise ValueError("This method is only supported for steady state simulations")
        links = ObjectCollection()
        for link in self.links:
            if (link.to_node == self and link.flow >= 0) or (link.from_node == self and link.flow < 0):
                links[link.uid] = link
                
        return links

    @property
    def downstream_links(self):
        """ return a list of downstream nodes """
        if self.results != {}:
            raise ValueError("This method is only supported for steady state simulations")

        links = ObjectCollection()
        for link in self.links:
            if (link.from_node == self and link.flow >= 0) or (link.to_node == self and link.flow < 0):
                links[link.uid] = link
        return links

    @property
    def inflow(self):
        outflow = 0
        for link in self.upstream_links:
            outflow += abs(link.flow)
        return outflow

    @property
    def outflow(self):
        outflow = 0
        for link in self.downstream_links:
            outflow += abs(link.flow)
        return outflow
        """ calculates all the water flowing out of the node """

class Reservoir(Node):
    """ EPANET Reservoir Class """
    node_type = "Reservoir"

class Junction(Node):
    """ EPANET Junction Class """
    static_properties = {'elevation': ep.EN_ELEVATION, 'basedemand': ep.EN_BASEDEMAND}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE, 'demand': ep.EN_DEMAND}
    node_type = "Junction"

    @property
    def pattern(self):
        pattern_index = self.get_property(ep.EN_PATTERN)
        uid = ep.ENgetpatternid(pattern_index)
        return Pattern(uid)

    @pattern.setter
    def pattern(self, value):
        if isinstance(value, int):
            pattern_index = value
        elif isinstance(value, str):
            pattern_index = ep.ENgetpatternindex(value)
        else:
            pattern_index = value.index

        self.set_object_value(self.uid, ep.EN_PATTERN, pattern_index)





class Tank(Node):
    """ EPANET Tank Class """
    node_type = "Tank"

    static_properties = {'elevation': ep.EN_ELEVATION, 'basedemand': ep.EN_BASEDEMAND,
                         'initvolume': ep.EN_INITVOLUME, 'diameter': ep.EN_TANKDIAM,
                         'minvolume': ep.EN_MINVOLUME, 'minlevel': ep.EN_MINLEVEL,
                         'maxlevel': ep.EN_MAXLEVEL, 'maxvolume': 25, 'tanklevel': ep.EN_TANKLEVEL}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE, 
                  'demand': ep.EN_DEMAND, 'volume': 24, 'level': ep.EN_TANKLEVEL}
