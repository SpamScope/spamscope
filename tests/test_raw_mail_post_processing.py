#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys
import unittest

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from src.modules import MAIL_PATH

# Set environment variables to change defaults:
# Example export SPAMASSASSIN_ENABLED=True

DEFAULTS = {"SPAMASSASSIN_ENABLED": "False"}
OPTIONS = ChainMap(os.environ, DEFAULTS)

mail_thug = os.path.join(base_path, 'samples', 'mail_thug')


class TestPostProcessing(unittest.TestCase):

    @unittest.skipIf(OPTIONS["SPAMASSASSIN_ENABLED"].capitalize() == "False",
                     "SpamAssassin test skipped: "
                     "set env variable 'SPAMASSASSIN_ENABLED' to True")
    def test_spamassassin(self):
        """Test add SpamAssassin processing."""

        from src.modules.mails import spamassassin

        conf = {"enabled": True}
        results = {}
        self.assertFalse(results)
        spamassassin(conf, mail_thug, MAIL_PATH, results)
        self.assertTrue(results)
        self.assertIn("spamassassin", results)
        self.assertIsInstance(results["spamassassin"], dict)
        self.assertIn("X-Spam-Checker-Version", results["spamassassin"])
        self.assertIn("X-Spam-Flag", results["spamassassin"])
        self.assertIn("X-Spam-Level", results["spamassassin"])
        self.assertIn("X-Spam-Status", results["spamassassin"])
        self.assertIn("score", results["spamassassin"])
        self.assertIn("details", results["spamassassin"])

    @unittest.skipIf(OPTIONS["SPAMASSASSIN_ENABLED"].capitalize() == "False",
                     "Complete post processing test skipped: "
                     "set env variable 'SPAMASSASSIN_ENABLED' to True")
    def test_processors(self):
        """Test all post processing."""

        from src.modules.mails import processors

        conf = {
            "spamassassin": {"enabled": True}}

        results = {}
        self.assertFalse(results)

        for p in processors:
            p(conf[p.__name__], mail_thug, MAIL_PATH, results)

        self.assertTrue(results)
        self.assertIn("spamassassin", results)


if __name__ == '__main__':
    unittest.main(verbosity=2)
