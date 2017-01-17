from . import epanet2 as ep
from .baseobject import BaseObject

class Pattern(object):

    def __init__(self, uid):
        self.uid = uid

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

    @property
    def index(self):
        return ep.ENgetpatternindex(self.uid)

    @property
    def values(self):
        values = []
        n_values = ep.ENgetpatternlen(self.index)
        for n in range(1, n_values+1):
            values.append(ep.ENgetpatternvalue(self.index, n))
        return values

    @values.setter
    def values(self, value):
        ep.ENsetpattern(self.index, value)
