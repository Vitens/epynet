import pandas as pd

class BaseObject(object):

    static_properties = {}
    properties = {}

    def __init__(self, uid):

        # the object index
        self.uid = uid
        # dictionary of static values
        self._static_values = {}
        # dictionary of calculation results, only gets
        # filled during solve() method
        self.results = {}
        # list of times
        self.times = []

    def get_index(self, uid):
        raise NotImplementedError

    def set_object_value(self, uid, code, value):
        raise NotImplementedError

    def get_object_value(self, uid, code):
        raise NotImplementedError

    def reset(self):
        self._static_values = {}
        self.results = {}
        self.times = []

    def __str__(self):
        return "<epynet."+self.__class__.__name__ + " with id '" + self.uid + "'>"

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
            super(BaseObject, self).__setattr__(name, value)

    def set_static_property(self, code, value):
        self._static_values[code] = value
        self.set_object_value(self.uid, code, value)

    def get_property(self, code):
        return self.get_object_value(self.uid, code)

    def get_static_property(self, code):
        if code not in self._static_values.keys():
            self._static_values[code] = self.get_property(code)
        return self._static_values[code]
