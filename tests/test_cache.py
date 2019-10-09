"""
Tests for a simple cache
"""

import unittest
from crossmap.cache import CrossmapCache


class CrossmapCacheTests(unittest.TestCase):
    """Creating an empty DB with basic structure"""

    def test_set_and_get(self):
        """simple addition and extraction from the cache"""

        cache = CrossmapCache(8)
        cache.set(0, 4, 10)
        cache.set(0, 8, 11)
        result, missing = cache.get(0, [4, 8])
        self.assertEqual(len(result), 2)
        self.assertEqual(result[4], 10)
        self.assertEqual(result[8], 11)

    def test_set_get_string_keys(self):
        """simple handling, using string keys"""

        cache = CrossmapCache(8)
        cache.set(0, "a", 10)
        cache.set(0, "b", 20)
        result0, m0 = cache.get(0, ["a", "b"])
        self.assertEqual(len(result0), 2)
        self.assertEqual(len(m0), 0)
        cache.clear()
        result1, m1 = cache.get(0, ["a", "b"])
        self.assertEqual(len(result1), 0)
        self.assertEqual(len(m1), 2)

    def test_report_missing(self):
        """simple addition and extraction from the cache"""

        cache = CrossmapCache(8)
        cache.set(0, 0, 10)
        cache.set(0, 1, 20)
        result, missing = cache.get(0, [0,2])
        self.assertEqual(len(result), 1)
        self.assertEqual(len(missing), 1)
        self.assertListEqual(missing, [2])

    def test_clear(self):
        """clearing cache leads to cache misses"""

        cache = CrossmapCache(8)
        cache.set(0, 0, 10)
        cache.set(0, 1, 20)
        result0, m0 = cache.get(0, [0, 1])
        self.assertEqual(len(result0), 2)
        self.assertEqual(len(m0), 0)
        cache.clear()
        result1, m1 = cache.get(0, [0, 1])
        self.assertEqual(len(result1), 0)
        self.assertEqual(len(m1), 2)

    def test_get_empty(self):
        """handling when request is empty"""

        cache = CrossmapCache()
        cache.set(0, "abc", 2)
        result, missing = cache.get(0, None)
        self.assertEqual(result, dict())
        self.assertEqual(missing, [])

    def test_deepcopy_get(self):
        """cache can be initialized to safeguarg against corruption"""

        cache = CrossmapCache(8)
        cache.set(0, 0, dict(a=3))
        cache.set(0, 1, dict(b=0))
        result0, _ = cache.get(0, [0])
        self.assertEqual(result0[0]["a"], 3)
        # attempt to corrupt the cache object
        result0[0]["a"] = 10
        result1, _ = cache.get(0, [0])
        self.assertEqual(result1[0]["a"], 3)

    def test_remove_old(self):
        """remove old elements when cache becomes full"""

        cache = CrossmapCache(32)
        for i in range(40):
            cache.set(0, i, i)
        # cache must remain bounded
        self.assertLessEqual(len(cache._cache), 32)
        # new elements should exist in cache, old ones not
        self.assertTrue((0, 38) in cache._cache)
        self.assertFalse((0, 0) in cache._cache)

