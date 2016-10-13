import collections
import pandas as pd

class TransformedDict(collections.MutableMapping):
    """A dictionary that applies an arbitrary key-altering
       function before accessing the keys.
       
       from: http://stackoverflow.com/questions/3387691/python-how-to-perfectly-override-a-dict
       """

    def __init__(self, *args, **kwargs):
        self.store = dict()
        self.update(dict(*args, **kwargs))  # use the free update to set keys

    def __getitem__(self, key):
        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        self.store[self.__keytransform__(key)] = value

    def __delitem__(self, key):
        del self.store[self.__keytransform__(key)]

    def __iter__(self):
        return iter(self.store.values())

    def __len__(self):
        return len(self.store)

    @staticmethod
    def __keytransform__(key):
        return key

class IndexIdType(TransformedDict):
    """ Index Id List/Dict hybrid that allows setting both
        str (id) and integer (index) values """

    def __getitem__(self, key):

        # support for index slicing through pandas
        if isinstance(key,pd.Series):
            indices = key[key==True].index
            return_dict = IndexIdType()
            for index in indices:
                obj = self.store[self.__keytransform__(index)]
                return_dict[obj.index] = obj
            return return_dict

        return self.store[self.__keytransform__(key)]

    def __setitem__(self, key, value):
        key = self.__keytransform__(key)
        self.store[key] = value
        self.store[key].index = key # the index of the entity is also saved as attribute in the item. 

    def __keytransform__(self, key):
        """ Change id key to index """

        if isinstance(key, str):
            for i, j in self.store.items():
                if key == j.uid:
                    return i
            raise KeyError("Key %s not found" % key)
        return key

    # magic methods to transform collection attributes to Pandas Series or, if we return classes, another list
    def __getattr__(self,name):

        values = {}

        for key, item in self.store.iteritems():
            values[item.uid] = getattr(item,name)

        if isinstance(values[item.uid], pd.Series):
            return pd.concat(values,axis=1)

        return pd.Series(values)

    def __setattr__(self, name, value):
        if name == "store":
            super(IndexIdType,self).__setattr__("store",value)
            return

        if isinstance(value, pd.Series):
            for key, item in self.store.iteritems():
                setattr(item,name,value[item.uid])
            return

        for key, item in self.store.iteritems():

            setattr(item,name,value)

