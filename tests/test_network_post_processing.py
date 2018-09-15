#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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

import logging
import os
import six
import unittest
import simplejson as json

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from context import DEFAULTS


OPTIONS = ChainMap(os.environ, DEFAULTS)

logging.getLogger().addHandler(logging.NullHandler())


class TestPostProcessing(unittest.TestCase):

    def setUp(self):
        self.ipaddress = "8.8.8.8"

    @unittest.skipIf(OPTIONS["VIRUSTOTAL_ENABLED"].capitalize() == "False",
                     "VirusTotal test skipped: "
                     "set env variable 'VIRUSTOTAL_ENABLED' to True")
    def test_virustotal(self):
        """Test add VirusTotal processing."""

        from context import networks

        virustotal = networks.virustotal

        conf = {"enabled": True,
                "api_key": OPTIONS["VIRUSTOTAL_APIKEY"]}
        results = {}
        self.assertFalse(results)
        virustotal(conf, self.ipaddress, results)
        self.assertTrue(results)
        self.assertIn("virustotal", results)
        self.assertIsInstance(results["virustotal"], six.text_type)
        r = json.loads(results["virustotal"])
        self.assertTrue(r)
        self.assertIsInstance(r, dict)

    @unittest.skipIf(OPTIONS["SHODAN_ENABLED"].capitalize() == "False",
                     "Shodan.io test skipped: "
                     "set env variable 'SHODAN_ENABLED' to True")
    def test_shodan(self):
        """Test add Shodan processing."""

        from context import networks

        shodan = networks.shodan

        # Complete parameters
        conf = {"enabled": True,
                "api_key": OPTIONS["SHODAN_APIKEY"]}
        results = {}
        self.assertFalse(results)
        shodan(conf, self.ipaddress, results)
        self.assertIn("shodan", results)
        self.assertIsInstance(results["shodan"], six.text_type)
        r = json.loads(results["shodan"])
        self.assertTrue(r)
        self.assertIsInstance(r, dict)
        self.assertIn("data", r)

        results = {}
        shodan(conf, "8.8.8", results)
        self.assertFalse(results)

    @unittest.skipIf(OPTIONS["SHODAN_ENABLED"].capitalize() == "False" or
                     OPTIONS["VIRUSTOTAL_ENABLED"].capitalize() == "False",
                     "Complete post processing test skipped: "
                     "set env variables 'SHODAN_ENABLED' and "
                     "'VIRUSTOTAL_ENABLED' to True")
    def test_processors(self):
        """Test all post processing."""

        from context import networks
        from operator import itemgetter

        p_ordered = [i[0] for i in sorted(
            networks.processors, key=itemgetter(1))]

        conf = {
            "virustotal": {"enabled": True,
                           "api_key": OPTIONS["VIRUSTOTAL_APIKEY"]},
            "shodan": {"enabled": True,
                       "api_key": OPTIONS["SHODAN_APIKEY"]}}

        results = {}
        self.assertFalse(results)

        for p in p_ordered:
            p(conf[p.__name__], self.ipaddress, results)

        self.assertTrue(results)
        self.assertIn("shodan", results)
        self.assertIsInstance(results["shodan"], six.text_type)
        self.assertIn("virustotal", results)
        self.assertIsInstance(results["virustotal"], six.text_type)


if __name__ == '__main__':
    unittest.main(verbosity=2)
