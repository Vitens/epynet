""" EPYNET Classes """
from . import epanet2
from .objectcollection import ObjectCollection
from .baseobject import BaseObject, lazy_property
from .pattern import Pattern


class Node(BaseObject):
    """ Base EPANET Node class """

    static_properties = {'elevation': epanet2.EN_ELEVATION}
    properties = {'elevation': epanet2.EN_ELEVATION, 'demand': epanet2.EN_DEMAND, 'head': epanet2.EN_HEAD,
                  'pressure': epanet2.EN_PRESSURE, 'quality': epanet2.EN_QUALITY}

    def __init__(self, uid, network):
        super(Node, self).__init__(uid, network)
        self.links = ObjectCollection()

    def get_index(self, uid):
        if not self._index:
            self._index = self.network().ep.ENgetnodeindex(uid)
        return self._index

    def set_object_value(self, code, value):
        return self.network().ep.ENsetnodevalue(self.index, code, value)

    def get_object_value(self, code):
        return self.network().ep.ENgetnodevalue(self.index, code)

    @property
    def comment(self):
        return self.network().ep.ENgetcomment(0, self.index)  # get comment from NODE table

    @comment.setter
    def comment(self, value):
        return self.network().ep.ENsetcomment(0, self.index, value)  # set comment from LINK table

    @property
    def index(self):
        return self.get_index(self.uid)

    @lazy_property
    def coordinates(self):
        return self.network().ep.ENgetcoord(self.index)

    # extra functionality
    @lazy_property
    def upstream_links(self):
        """ return a list of upstream links """
        if self.results != {}:
            raise ValueError("This method is only supported for steady state simulations")

        links = ObjectCollection()
        for link in self.links:
            if (link.to_node == self and link.flow >= 1e-3) or (link.from_node == self and link.flow < -1e-3):
                links[link.uid] = link
        return links

    @lazy_property
    def downstream_links(self):
        """ return a list of downstream nodes """
        if self.results != {}:
            raise ValueError("This method is only supported for steady state simulations")

        links = ObjectCollection()
        for link in self.links:
            if (link.from_node == self and link.flow >= 1e-3) or (link.to_node == self and link.flow < -1e-3):
                links[link.uid] = link
        return links

    @lazy_property
    def inflow(self):
        """ calculates all the water flowing in the node
        """
        outflow = 0
        for link in self.upstream_links:
            outflow += abs(link.flow)
        return outflow

    @lazy_property
    def outflow(self):
        """ calculates all the water flowing out of the node
        """
        outflow = 0
        for link in self.downstream_links:
            outflow += abs(link.flow)
        return outflow


class Reservoir(Node):
    """ EPANET Reservoir Class """
    node_type = "Reservoir"


class Junction(Node):
    """ EPANET Junction Class """
    static_properties = {'elevation': epanet2.EN_ELEVATION, 'basedemand': epanet2.EN_BASEDEMAND,
                         'emitter': epanet2.EN_EMITTER}
    properties = {'head': epanet2.EN_HEAD, 'pressure': epanet2.EN_PRESSURE, 'demand': epanet2.EN_DEMAND,
                  'quality': epanet2.EN_QUALITY}
    node_type = "Junction"

    @property
    def pattern(self):
        pattern_index = int(self.get_property(epanet2.EN_PATTERN))
        uid = self.network().ep.ENgetpatternid(pattern_index)
        return Pattern(uid, self.network())

    @pattern.setter
    def pattern(self, value):
        if isinstance(value, int):
            pattern_index = value
        elif isinstance(value, str):
            pattern_index = self.network().ep.ENgetpatternindex(value)
        else:
            pattern_index = value.index

        self.network().solved = False
        self.set_object_value(epanet2.EN_PATTERN, pattern_index)


class Tank(Node):
    """ EPANET Tank Class """
    node_type = "Tank"

    static_properties = {'elevation': epanet2.EN_ELEVATION, 'basedemand': epanet2.EN_BASEDEMAND,
                         'initvolume': epanet2.EN_INITVOLUME, 'diameter': epanet2.EN_TANKDIAM,
                         'minvolume': epanet2.EN_MINVOLUME, 'minlevel': epanet2.EN_MINLEVEL,
                         'maxlevel': epanet2.EN_MAXLEVEL, 'maxvolume': epanet2.EN_MAXVOLUME,
                         'tanklevel': epanet2.EN_TANKLEVEL}
    properties = {'head': epanet2.EN_HEAD, 'pressure': epanet2.EN_PRESSURE,
                  'demand': epanet2.EN_DEMAND, 'volume': epanet2.EN_TANKVOLUME, 'level': epanet2.EN_TANKLEVEL}
