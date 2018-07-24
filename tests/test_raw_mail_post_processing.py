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
import unittest

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap

from context import MAIL_PATH, DEFAULTS

OPTIONS = ChainMap(os.environ, DEFAULTS)

base_path = os.path.realpath(os.path.dirname(__file__))
mail_thug = os.path.join(base_path, 'samples', 'mail_thug')


logging.getLogger().addHandler(logging.NullHandler())


class TestPostProcessing(unittest.TestCase):

    @unittest.skipIf(OPTIONS["SPAMASSASSIN_ENABLED"].capitalize() == "False",
                     "SpamAssassin test skipped: "
                     "set env variable 'SPAMASSASSIN_ENABLED' to True")
    def test_spamassassin(self):
        """Test add SpamAssassin processing."""

        from context import mails

        spamassassin = mails.spamassassin

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

        from context import mails
        from operator import itemgetter

        p_ordered = [i[0] for i in sorted(mails.processors, key=itemgetter(1))]

        conf = {
            "spamassassin": {"enabled": True}}

        results = {}
        self.assertFalse(results)

        for p in p_ordered:
            p(conf[p.__name__], mail_thug, MAIL_PATH, results)

        self.assertTrue(results)
        self.assertIn("spamassassin", results)


if __name__ == '__main__':
    unittest.main(verbosity=2)
