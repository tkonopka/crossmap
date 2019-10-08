"""
A simple cache object that uses a pair of integers as keys.

This is a sloppy cache by default. The values are not deep-copied
during get() and set(). This means the cache can become corrupt if objects
are changed outside.

The cache can be initialized with deepcopy=True. In that case, the
cache guarantees that get() are separate from what is stored in the cache.
"""


from copy import deepcopy as deepc
from math import floor
from time import time


class CrossmapCache:
    """Management for a cache"""

    def __init__(self, max_size=8192, deepcopy=False):
        """sets up path to db, operations performed via functions"""

        self.max_size = max(32, max_size)
        if deepcopy:
            self._copy = deepc
        else:
            self._copy = lambda x: x
        self._cache = dict()

    def _make_space(self, num_items):
        """remove some least-recently used items"""

        time_keys = [(v[0], k) for k, v in self._cache.items()]
        time_keys.sort()
        for i in range(num_items):
            self._cache.pop(time_keys[i][1])

    def set(self, k1, k2, data):
        """set the contents of a cache

        :param k1: integer, first identifier
        :param k2: integer, second identifier
        :param data: any data object
        """

        if len(self._cache) >= self.max_size:
            self._make_space(floor(self.max_size/8))
        self._cache[(k1, k2)] = (time(), self._copy(data))

    def clear(self):
        """remove all content from the cache"""

        self._cache = dict()

    def get(self, k1, k2s):
        """get data from the cache

        :param k1: integer, first identifier
        :param k2s: list of integers, second identifiers
        :return: two items; a dict with data for items available from cache,
            a list of indexes not available through the cache
        """

        result, missing = dict(), []
        if k2s is None:
            k2s = []
        cache = self._cache
        copy = self._copy
        for k2 in k2s:
            key = (k1, k2)
            if key in cache:
                value = cache[key][1]
                cache[key] = (time(), value)
                result[k2] = copy(value)
            else:
                missing.append(k2)
        return result, missing

