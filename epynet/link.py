""" EPYNET Classes """
import epanet2 as ep
from baseobject import BaseObject


class Link(BaseObject):
    """ EPANET Link Class """

    properties = {'flow': ep.EN_FLOW}

    def __init__(self, index):
        super(Link, self).__init__(index)
        self.from_node = None
        self.to_node = None

    def get_uid(self, index):
        return ep.ENgetlinkid(index)

    def set_object_value(self, index, code, value):
        return ep.ENsetlinkvalue(index, code, value)

    def get_object_value(self, index, code):
        return ep.ENgetlinkvalue(index, code)

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

    static_properties = {'diameter': ep.EN_DIAMETER, 'length': ep.EN_LENGTH,
                         'roughness': ep.EN_ROUGHNESS, 'minorloss': ep.EN_MINORLOSS,
                         'status': ep.EN_STATUS}
    properties = {'flow': ep.EN_FLOW, 'headloss': ep.EN_HEADLOSS, 'velocity': ep.EN_VELOCITY}


class Pump(Link):
    """ EPANET Pump Class """
    link_type = 'pump'

    static_properties = {'length': ep.EN_LENGTH, 'speed': ep.EN_INITSETTING}
    properties = {'flow': ep.EN_FLOW}

    @property
    def velocity(self):
        return 1.0


class Valve(Link):
    """ EPANET Valve Class """

    static_properties = {'setting': ep.EN_INITSETTING}
    properties = {'velocity': ep.EN_VELOCITY, 'flow': ep.EN_FLOW}

    link_type = 'valve'

    types = {3: "PRV", 4: "PSV", 5: "PBV", 6: "FCV", 7: "TCV", 8: "GPV"}

    @property
    def valve_type(self):
        type_code = ep.ENgetlinktype(self.index)
        return self.types[type_code]
