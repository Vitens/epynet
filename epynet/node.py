""" EPYNET Classes """
import epanet2 as ep
from objectcollection import ObjectCollection
from baseobject import BaseObject

class Node(BaseObject):
    """ Base EPANET Node class """

    static_properties = {'elevation': ep.EN_ELEVATION}
    properties = {'head': ep.EN_HEAD, 'pressure': ep.EN_PRESSURE}

    def __init__(self, index):
        super(Node, self).__init__(index)
        self.links = ObjectCollection()

    def get_uid(self, index):
        return ep.ENgetnodeid(index)

    def set_object_value(self, index, code, value):
        return ep.ENsetnodevalue(index, code, value)

    def get_object_value(self, index, code):
        return ep.ENgetnodevalue(index, code)

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
        if len(self.upstream_links) == 0:
            return 0
        """ calculates all the water flowing into the node """
        return self.upstream_links.flow.abs().sum()

    @property
    def outflow(self):
        if len(self.downstream_links) == 0:
            return 0
        """ calculates all the water flowing out of the node """
        return self.downstream_links.flow.abs().sum()

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
