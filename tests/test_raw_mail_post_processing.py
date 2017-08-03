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
import six
import sys
import unittest
import simplejson as json

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

# Set environment variables to change defaults:
# Example export VIRUSTOTAL_APIKEY=your_api_key

DEFAULTS = {"SPAMASSASSIN_ENABLED": "False"}
OPTIONS = ChainMap(os.environ, DEFAULTS)


class TestPostProcessing(unittest.TestCase):

    def setUp(self):
        pass

    @unittest.skipIf(OPTIONS["SPAMASSASSIN_ENABLED"].capitalize() == "False",
                     "SpamAssassin test skipped: "
                     "set env variable 'SPAMASSASSIN_ENABLED' to True")
    def test_spamassassin(self):
        """Test add SpamAssassin processing."""

        from src.modules.mails import spamassassin

        conf = {"enabled": True}
        results = {}
        self.assertFalse(results)
        spamassassin(conf, mail_thug, mail_type, results)
        self.assertTrue(results)
        self.assertIn("spamassassin", results)
        self.assertIsInstance(results["spamassassin"], dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
