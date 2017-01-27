#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

import copy
import datetime
import os
import sys
import unittest

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)

import src.modules.utils as utils
from src.modules.attachments import MailAttachments
from src.modules.exceptions import ImproperlyConfigured
from mailparser import MailParser

text_files = os.path.join(base_path, 'samples', 'lorem_ipsum.txt')
mail = os.path.join(base_path, 'samples', 'mail_thug')


class TestSearchText(unittest.TestCase):

    def setUp(self):
        self.f = utils.reformat_output

        p = MailParser()
        p.parse_from_file(mail)
        self.mail_obj = p.parsed_mail_obj
        self.mail_obj['analisys_date'] = datetime.datetime.utcnow().isoformat()

        self.attachments = MailAttachments.withhashes(p.attachments_list)
        self.attachments.run()

        self.parameters = {
            'elastic_index_mail': "spamscope_mails-",
            'elastic_type_mail': "spamscope",
            'elastic_index_attach': "spamscope_attachments-",
            'elastic_type_attach': "spamscope"}

    def test_search_words_in_text(self):
        with open(text_files) as f:
            text = f.read()

        keywords_1 = [
            "nomatch",
            "nomatch"]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_1), False)

        keywords_2 = [
            "nomatch",
            "nomatch",
            "theophrastus rationibus"]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2), True)

        keywords_2 = [
            "nomatch",
            "theophrastus nomatch"]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2), False)

        keywords_2 = ["theophrastus quo vidit"]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2), True)

    def test_reformat_output_first(self):

        with self.assertRaises(ImproperlyConfigured):
            self.f(mail=self.mail_obj)

        with self.assertRaises(KeyError):
            self.f(mail=self.mail_obj, bolt="output-elasticsearch")

        m, a = self.f(
            mail=self.mail_obj, bolt="output-elasticsearch", **self.parameters)

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 1)
        self.assertIsInstance(a[0], dict)
        self.assertIn('@timestamp', m)
        self.assertIn('_index', a[0])
        self.assertIn('_type', a[0])
        self.assertIn('type', a[0])

        # Mail
        self.assertIsInstance(m, dict)
        self.assertIn('@timestamp', m)
        self.assertIn('_index', m)
        self.assertIn('_type', m)
        self.assertIn('type', m)

    def test_reformat_output_second(self):
        m = copy.deepcopy(self.mail_obj)
        m['attachments'] = list(self.attachments)

        m, a = self.f(
            mail=m, bolt="output-elasticsearch", **self.parameters)

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 2)

        self.assertIsInstance(a[0], dict)
        self.assertIn('@timestamp', a[0])
        self.assertIn('_index', a[0])
        self.assertIn('_type', a[0])
        self.assertIn('type', a[0])
        self.assertIn('payload', a[0])
        self.assertEqual(a[0]['is_archived'], True)

        self.assertIsInstance(a[1], dict)
        self.assertIn('@timestamp', a[1])
        self.assertIn('_index', a[1])
        self.assertIn('_type', a[1])
        self.assertIn('type', a[1])
        self.assertIn('files', a[1])
        self.assertIn('payload', a[1])
        # self.assertIn('tika', a[1])
        self.assertNotIn('payload', a[1]['files'][0])
        self.assertEqual(a[1]['is_archived'], False)
        self.assertEqual(a[1]['is_archive'], True)

        # Mail
        self.assertIsInstance(m, dict)
        self.assertIn('@timestamp', m)

    def test_reformat_output_third(self):
        m = copy.deepcopy(self.mail_obj)
        m['attachments'] = list(self.attachments)

        m, a = self.f(mail=m, bolt="output-redis")

        # Attachments
        self.assertIsInstance(a, list)
        self.assertEqual(len(a), 2)

        self.assertIsInstance(a[0], dict)
        self.assertNotIn('@timestamp', a[0])
        self.assertNotIn('_index', a[0])
        self.assertNotIn('_type', a[0])
        self.assertNotIn('type', a[0])
        self.assertIn('payload', a[0])
        self.assertEqual(a[0]['is_archived'], True)

        self.assertIsInstance(a[1], dict)
        self.assertNotIn('@timestamp', a[1])
        self.assertNotIn('_index', a[1])
        self.assertNotIn('_type', a[1])
        self.assertNotIn('type', a[1])
        self.assertIn('files', a[1])
        self.assertIn('payload', a[1])
        # self.assertIn('tika', a[1])
        self.assertNotIn('payload', a[1]['files'][0])
        self.assertEqual(a[1]['is_archived'], False)
        self.assertEqual(a[1]['is_archive'], True)

        # Mail
        self.assertIsInstance(m, dict)
        self.assertNotIn('@timestamp', m)
        self.assertNotIn('_index', m)
        self.assertNotIn('_type', m)
        self.assertNotIn('type', m)

    def test_load_keywords_list(self):
        d = {"generic": "conf/keywords/subjects.example.yml",
             "custom": "conf/keywords/subjects_english.example.yml"}
        results = utils.load_keywords_list(d)
        self.assertIsInstance(results, set)
        self.assertIn("fattura", results)
        self.assertIn("conferma", results)

        with self.assertRaises(ImproperlyConfigured):
            d = {"generic": "conf/keywords/targets.example.yml"}
            results = utils.load_keywords_list(d)

    def test_load_keywords_dict(self):
        d = {"generic": "conf/keywords/targets.example.yml",
             "custom": "conf/keywords/targets_english.example.yml"}
        results = utils.load_keywords_dict(d)
        self.assertIsInstance(results, dict)
        self.assertIn("Banca Tizio", results)
        self.assertNotIn("banca tizio", results)
        self.assertIn("tizio", results["Banca Tizio"])
        self.assertIn("caio rossi", results["Banca Tizio"])

        with self.assertRaises(ImproperlyConfigured):
            d = {"generic": "conf/keywords/subjects.example.yml"}
            results = utils.load_keywords_dict(d)


if __name__ == '__main__':
    unittest.main()
