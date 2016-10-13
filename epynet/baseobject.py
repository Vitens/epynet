class BaseObject(object):

    static_properties = {}
    properties = {}

    def __init__(self, index):

        # the object index
        self.index = index
        # the object id
        self.uid = self.get_uid(index)
        # dictionary of static values
        self._static_values = {}
        # dictionary of calculation results, only gets
        # filled during solve() method
        self.results = {}
        # list of times
        self.times = []

    def get_id(self, index):
        raise NotImplementedError

    def reset(self):
        self._static_values = {}
        self.results = {}
        self.times = []

    def __str__(self):
        return self.uid
    
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
