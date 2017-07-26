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

import mailparser
from pyfaup.faup import Faup

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)

import src.modules.mails.phishing as phishing
import src.modules.utils as utils

mail_thug = os.path.join(base_path, 'samples', 'mail_thug')
mail_form = os.path.join(base_path, 'samples', 'mail_form')


class TestPhishing(unittest.TestCase):
    faup = Faup()

    def setUp(self):
        parser = mailparser.parse_from_file(mail_thug)
        self.email = parser.parsed_mail_obj
        self.attachments = parser.attachments_list

        parser = mailparser.parse_from_file(mail_form)
        self.email_form = parser.parsed_mail_obj

        body = self.email_form.get("body")
        self.urls = utils.urls_extractor(self.faup, body)

        d = {"generic": "conf/keywords/targets.example.yml",
             "custom": "conf/keywords/targets_english.example.yml"}
        self.targets = utils.load_keywords_dict(d)

        d = {"generic": "conf/keywords/subjects.example.yml",
             "custom": "conf/keywords/subjects_english.example.yml"}
        self.subjects = utils.load_keywords_list(d)

    def test_check_check_form(self):
        body = self.email_form.get("body")
        flag_form = phishing.check_form(body)
        self.assertTrue(flag_form)

        body = self.email.get("body")
        flag_form = phishing.check_form(body)
        self.assertFalse(flag_form)

    def test_check_urls(self):
        flag = False
        if any(phishing.check_urls(self.urls, i)
               for i in self.targets.values()):
            flag = True

        self.assertTrue(flag)

    def test_check_phishing(self):
        results = phishing.check_phishing(
            email=self.email,
            attachments=self.attachments,
            urls_body=self.urls,
            urls_attachments=self.urls,
            target_keys=self.targets,
            subject_keys=self.subjects)

        self.assertIsInstance(results, dict)
        self.assertEqual(results["score"], 123)
        self.assertIn("filename_attachments", results["score_expanded"])
        self.assertIn("mail_subject", results["score_expanded"])
        self.assertIn("mail_body", results["score_expanded"])
        self.assertIn("mail_from", results["score_expanded"])
        self.assertIn("urls_body", results["score_expanded"])
        self.assertIn("urls_attachments", results["score_expanded"])
        self.assertIn("Test", results["targets"])
        self.assertTrue(results["with_phishing"])


if __name__ == '__main__':
    unittest.main(verbosity=2)
