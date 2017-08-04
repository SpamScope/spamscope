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

import src.modules.mails.spamassassin_analysis as spamassassin

mail_thug = os.path.join(base_path, 'samples', 'mail_thug')
mail_thug_spamassassin = os.path.join(
    base_path, 'samples', 'mail_thug_spamassassin')
mail_spamassassin = os.path.join(base_path, 'samples', 'mail_spamassassin')


class TestSpamAssassin(unittest.TestCase):

    def test_obj_report(self):
        with open(mail_thug_spamassassin) as f:
            s = f.read()

        report = spamassassin.obj_report(s)
        self.assertIsInstance(report, dict)
        self.assertIn("X-Spam-Checker-Version", report)
        self.assertIn("X-Spam-Flag", report)
        self.assertIn("X-Spam-Level", report)
        self.assertIn("X-Spam-Status", report)
        self.assertIn("score", report)
        self.assertIn("details", report)
        self.assertIsInstance(report["details"], list)
        self.assertIsInstance(report["score"], float)
        self.assertEqual(report["score"], 5.8)
        self.assertEqual(len(report["details"]), 3)

    def test_analysis_from_file(self):
        s = spamassassin.analysis_from_file(mail_thug)
        self.assertIn("X-Spam-Status", s)
        self.assertIn("pts rule name", s)

    def test_report_from_file(self):
        s = spamassassin.report_from_file(mail_thug)
        self.assertIsInstance(s, dict)
        self.assertIn("X-Spam-Status", s)
        self.assertIn("score", s)
        self.assertIn("details", s)
        self.assertIsInstance(s["details"], list)
        self.assertIsInstance(s["score"], float)

    def test_mail_spamassassin(self):
        s = spamassassin.report_from_file(mail_spamassassin)
        self.assertIsInstance(s, dict)
        self.assertIn("X-Spam-Status", s)
        self.assertIn("score", s)
        self.assertIn("details", s)
        self.assertIsInstance(s["details"], list)
        self.assertIsInstance(s["score"], float)


if __name__ == '__main__':
    unittest.main(verbosity=2)
