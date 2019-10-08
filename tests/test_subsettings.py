"""
Tests for parsing sub-settings (features, server, tokens, etc.)

(Some of these are only stubs; they can be expanded when the
classes start performing stronger validation)
"""

import unittest
from os.path import join
from crossmap.settings import CrossmapLoggingSettings
from crossmap.settings import CrossmapFeatureSettings
from crossmap.settings import CrossmapTokenSettings
from crossmap.settings import CrossmapServerSettings
from crossmap.settings import CrossmapDiffusionSettings
from crossmap.settings import CrossmapCacheSettings


class CrossmapSettingsDiffusionTests(unittest.TestCase):
    """parsing settings for diffusion"""

    def setUp(self):
        self.default = CrossmapDiffusionSettings()
        self.custom = CrossmapDiffusionSettings({"threshold": 0.5})

    def test_threshold(self):
        """file set nonzero diffusion threshold"""

        self.assertEqual(self.default.threshold, 0)
        self.assertGreater(self.custom.threshold, 0.0)

    def test_str(self):
        """can construct a str representation"""

        self.assertTrue("Diffusion" in str(self.default))


class CrossmapFeaturesSettingsTests(unittest.TestCase):
    """Recording settings for handling features within crossmap analysis"""

    def setUp(self):
        self.default = CrossmapFeatureSettings()
        custom = {"max_number": 200,
                  "decoy": 0,
                  "weighting": [0.5, 0.5],
                  "aux": [1, 0.2]}
        self.custom = CrossmapFeatureSettings(custom)

    def test_features_number(self):
        """By default max number of features is 0"""

        self.assertEqual(self.default.max_number, 0)
        self.assertEqual(self.custom.max_number, 200)

    def test_weighting(self):
        """configure weight assigned to auxiliary data fields"""

        self.assertEqual(self.default.weighting[0], 1)
        self.assertEqual(self.custom.weighting[1], 0.5)

    def test_aux(self):
        """configure weights for aux_pos and aux_neg relative to data"""

        self.assertEqual(self.default.aux[0], 0.5)
        self.assertEqual(self.default.aux[1], 0.5)
        self.assertEqual(self.custom.aux[0], 1)
        self.assertEqual(self.custom.aux[1], 0.2)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("0.5" in str(self.custom))

    def test_map_file(self):
        """declare a file source for features"""

        self.assertEqual(self.default.map_file, None)
        with_map = CrossmapFeatureSettings({"map": "table.tsv"}, "crossmap")
        self.assertEqual(with_map.map_file, join("crossmap", "table.tsv"))


class CrossmapTokenSettingsTests(unittest.TestCase):
    """Settings related to tokenizing documents"""

    def setUp(self):
        self.default = CrossmapTokenSettings()
        self.custom = CrossmapTokenSettings({"k": 8, "alphabet": "abcde"})

    def test_k(self):
        """length of kmers"""

        self.assertEqual(self.default.k, 5)
        self.assertEqual(self.custom.k, 8)

    def test_alphabet(self):
        """settings are transfered from file into settings object"""

        # default alphabet
        self.assertEqual(self.default.alphabet, None)
        # custom alphabet
        self.assertTrue("e" in self.custom.alphabet)
        self.assertFalse("i" in self.custom.alphabet)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("abc" in str(self.custom))


class CrossmapServerSettingsTests(unittest.TestCase):
    """Settings related to configuring servers"""

    def setUp(self):
        ports = {"api_port": 8080, "ui_port": 8081 }
        self.custom = CrossmapServerSettings(ports)

    def test_ports(self):
        """settings extract port numbers"""

        self.assertEqual(self.custom.api_port, 8080)
        self.assertEqual(self.custom.ui_port, 8081)

    def test_str(self):
        """summarize settings in a string"""

        self.assertTrue("8081" in str(self.custom))


class CrossmapLoggingSettingsTests(unittest.TestCase):
    """Settings related to configuring logging"""

    def setUp(self):
        self.default = CrossmapLoggingSettings()
        custom = {"level": "INFO", "progress": 100}
        self.custom = CrossmapLoggingSettings(custom)

    def test_level(self):
        """settings logging detail"""

        self.assertEqual(self.default.level, "WARNING")
        self.assertEqual(self.custom.level, "INFO")

    def test_progress_interval(self):
        """settings for how often to report progress"""

        self.assertGreater(self.default.progress, 1000)
        self.assertEqual(self.custom.progress, 100)


class CrossmapCacheTests(unittest.TestCase):
    """parsing settings for caching items from the database"""

    def setUp(self):
        self.default = CrossmapCacheSettings()
        custom = {"counts": 256, "ids": 128,
                  "titles": 128, "data": 1024}
        self.custom = CrossmapCacheSettings(custom)

    def test_sizes(self):
        """parsing cache sizes"""

        self.assertEqual(self.custom.counts, 256)
        self.assertEqual(self.custom.ids, 128)
        self.assertEqual(self.custom.titles, 128)
        self.assertEqual(self.custom.data, 1024)

