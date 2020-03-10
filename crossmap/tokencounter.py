"""
Counter object that tracks values as well as number of updates
"""


class TokenCounter:
    """a dictionary counting values and number of updates"""

    def __init__(self):
        self.data = dict()
        self.count = dict()

    def add(self, key, value, count=1):
        """update a value

        :param key: object, key in dictionaries
        :param value: numeric value will be added to
            current value associated with the key
        :param count: integer, count associated with this transaction
        """

        if key not in self.data:
            self.data[key] = 0.0
            self.count[key] = 0
        self.data[key] += value
        self.count[key] += count

    def update(self, counter):
        """update self using another counter

        :param counter: a TokenCounter object
        """

        for k in counter.data.keys():
            self.add(k, counter.data[k], counter.count[k])

    def __len__(self):
        """fetch number of keys stored in this counter"""

        return len(self.data)

    def __contains__(self, key):
        """check if object has a key, using 'in'"""

        return key in self.data

    def keys(self):
        """access to an iterator over the keys stored in the object"""

        return self.data.keys()

    def __str__(self):
        """display a summary of the counted tokens"""
        result = ["TokenCounter"]
        for k in self.data.keys():
            print(str(k))
            result.append(str(self.data[k]) + "\t" + str(self.count[k]))
        return "\n".join(result)

