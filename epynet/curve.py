import epanet2 as ep
from baseobject import BaseObject

class Curve(object):

    def __init__(self, uid):
        self.uid = uid

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

    @property
    def index(self):
        return ep.ENgetcurveindex(self.uid)

    @property
    def values(self):
        return ep.ENgetcurve(self.index)

    @values.setter
    def values(self, value):
        ep.ENsetcurve(self.index, value)
