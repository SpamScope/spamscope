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

DEFAULTS = {"VIRUSTOTAL_ENABLED": "False",
            "SHODAN_ENABLED": "False"}

OPTIONS = ChainMap(os.environ, DEFAULTS)


class TestPostProcessing(unittest.TestCase):

    def setUp(self):
        self.ipaddress = "8.8.8.8"

    @unittest.skipIf(OPTIONS["VIRUSTOTAL_ENABLED"].capitalize() == "False",
                     "VirusTotal test skipped: "
                     "set env variable 'VIRUSTOTAL_ENABLED' to True")
    def test_virustotal(self):
        """Test add VirusTotal processing."""

        from src.modules.networks import virustotal

        conf = {"enabled": True,
                "api_key": OPTIONS["VIRUSTOTAL_APIKEY"]}
        results = {}
        self.assertFalse(results)
        virustotal(conf, self.ipaddress, results)
        self.assertTrue(results)
        self.assertIn("virustotal", results)
        self.assertIsInstance(results["virustotal"], dict)

    @unittest.skipIf(OPTIONS["SHODAN_ENABLED"].capitalize() == "False",
                     "Shodan.io test skipped: "
                     "set env variable 'SHODAN_ENABLED' to True")
    def test_shodan(self):
        """Test add Shodan processing."""

        from src.modules.networks import shodan

        # Complete parameters
        conf = {"enabled": True,
                "api_key": OPTIONS["SHODAN_APIKEY"]}

        results = {}
        self.assertFalse(results)
        results_str = json.dumps(results, ensure_ascii=False)
        self.assertTrue(results_str)

        shodan(conf, self.ipaddress, results)

        results_str = json.dumps(results, ensure_ascii=False)
        self.assertTrue(results)
        self.assertIn("shodan", results)
        self.assertIsInstance(results["shodan"], dict)
        self.assertIn("data", results["shodan"])
        self.assertEqual(results["shodan"]["city"], "Mountain View")

        results_converted = json.loads(results_str)
        self.assertTrue(results_converted)
        self.assertIn("shodan", results_converted)
        self.assertIsInstance(results_converted["shodan"], dict)
        self.assertIn("data", results_converted["shodan"])
        self.assertEqual(results_converted["shodan"]["city"], "Mountain View")

    @unittest.skipIf(OPTIONS["SHODAN_ENABLED"].capitalize() == "False",
                     "Shodan.io test skipped: "
                     "set env variable 'SHODAN_ENABLED' to True")
    def test_shodan_convert(self):
        """Test add Shodan processing."""

        from src.modules.networks import shodan

        # Complete parameters
        conf = {"enabled": True,
                "api_key": OPTIONS["SHODAN_APIKEY"]}
        results = {}
        self.assertFalse(results)
        shodan(conf, self.ipaddress, results)
        self.assertTrue(results)
        self.assertIn("shodan", results)
        self.assertIsInstance(results["shodan"], dict)

    @unittest.skipIf(OPTIONS["SHODAN_ENABLED"].capitalize() == "False" or
                     OPTIONS["VIRUSTOTAL_ENABLED"].capitalize() == "False",
                     "Complete post processing test skipped: "
                     "set env variables 'SHODAN_ENABLED' and "
                     "'VIRUSTOTAL_ENABLED' to True")
    def test_processors(self):
        """Test all post processing."""

        from src.modules.networks import processors

        conf = {
            "virustotal": {"enabled": True,
                           "api_key": OPTIONS["VIRUSTOTAL_APIKEY"]},
            "shodan": {"enabled": True,
                       "api_key": OPTIONS["SHODAN_APIKEY"]}}

        results = {}
        self.assertFalse(results)

        for p in processors:
            p(conf[p.__name__], self.ipaddress, results)

        self.assertTrue(results)
        self.assertIn("shodan", results)
        self.assertIsInstance(results["shodan"], dict)
        self.assertIn("virustotal", results)
        self.assertIsInstance(results["virustotal"], dict)


if __name__ == '__main__':
    unittest.main(verbosity=2)
