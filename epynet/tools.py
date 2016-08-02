import collections

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
