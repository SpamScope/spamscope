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

import datetime
import os
import sys
import unittest

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
mail_test1 = os.path.join(root, 'unittest', 'mails', 'mail_test1')
mail_test2 = os.path.join(root, 'unittest', 'mails', 'mail_test2')
mail_test3 = os.path.join(root, 'unittest', 'mails', 'mail_test3')
mail_malformed = os.path.join(root, 'unittest', 'mails', 'mail_malformed')
sys.path.append(root)
import src.modules.mail_parser as mail_parser


class TestMailParser(unittest.TestCase):
    parser = mail_parser.MailParser()

    def test_valid_mail(self):
        self.assertRaises(
            mail_parser.InvalidMail,
            self.parser.parse_from_string,
            "fake mail"
        )

    def test_valid_date_mail(self):
        self.assertRaises(
            mail_parser.InvalidDateMail,
            self.parser.parse_from_file,
            mail_test2,
        )

    def test_failed_parsing_date_mail(self):
        self.assertRaises(
            mail_parser.FailedParsingDateMail,
            self.parser.parse_from_file,
            mail_test3,
        )

    def test_parsing_know_values(self):
        self.parser.parse_from_file(mail_test1)

        raw = "<4516257BC5774408ADC1263EEBBBB73F@ad.regione.vda.it>"
        result = self.parser.message_id
        self.assertEqual(raw, result)

        raw = "mporcile@server_mail.it"
        result = self.parser.to_
        self.assertEqual(raw, result)

        raw = "<meteo@regione.vda.it>"
        result = self.parser.from_
        self.assertEqual(raw, result)

        raw = "Bollettino Meteorologico del 29/11/2015"
        result = self.parser.subject
        self.assertEqual(raw, result)

        result = self.parser.has_defects
        self.assertEqual(False, result)

        result = len(self.parser.attachments_list)
        self.assertEqual(3, result)

        raw = "Sun, 29 Nov 2015 09:45:18 +0100"
        raw_utc = datetime.datetime(
            2015, 11, 29, 8, 45, 18, 0
        ).isoformat()
        result = self.parser.date_mail.isoformat()
        self.assertEqual(raw_utc, result)

    def test_types(self):
        self.parser.parse_from_file(mail_test1)

        result = self.parser.parsed_mail_obj
        self.assertIsInstance(result, dict)

        result = self.parser.parsed_mail_json
        self.assertIsInstance(result, unicode)

        result = self.parser.random_message_id
        self.assertIsInstance(result, unicode)

        result = self.parser.headers
        self.assertIsInstance(result, unicode)

        result = self.parser.body
        self.assertIsInstance(result, unicode)

        result = self.parser.date_mail
        self.assertIsInstance(result, datetime.datetime)

        result = self.parser.from_
        self.assertIsInstance(result, unicode)

    def test_defects(self):
        self.parser.parse_from_file(mail_malformed)
        self.assertEqual(True, self.parser.has_defects)

if __name__ == '__main__':
    unittest.main()