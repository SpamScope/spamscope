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

import os
import sys
import unittest
from mailparser import MailParser

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
mail = os.path.join(base_path, 'samples', 'mail_malformed_1')
sys.path.append(root)
import src.modules.sample_parser as sp


class TestTikaProcessing(unittest.TestCase):

    def setUp(self):

        # Init
        p = MailParser()
        s = sp.SampleParser()
        self.tika = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.14.jar",
            valid_content_types=['application/zip'],
            memory_allocation=None)

        # Parsing mail
        p.parse_from_file(mail)
        self.attachments = []

        for i in p.attachments_list:
            s.parse_sample_from_base64(
                data=i['payload'],
                filename=i['filename'],
                mail_content_type=i['mail_content_type'],
                transfer_encoding=i['content_transfer_encoding'])
            self.attachments.append(s.result)

    def test_meta_data(self):
        """Test meta data analysis."""

        # Tika analysis
        self.tika.valid_content_types = []
        for i in self.attachments:
            self.tika.process(i)
            self.assertNotIn('tika', i)

        self.tika.valid_content_types = ['application/zip']
        for i in self.attachments:
            self.tika.process(i)
            self.assertIn('tika', i)

    def test_invalid_attachments(self):
        """Test InvalidAttachments exception."""

        self.tika.valid_content_types = ['application/zip']
        with self.assertRaises(sp.InvalidAttachment):
            self.tika.process([])

    def test_properties(self):
        """Test properties output."""

        self.tika.valid_content_types = ['application/zip']

        self.assertEqual(self.tika.jar, "/opt/tika/tika-app-1.14.jar")
        self.assertEqual(self.tika.memory_allocation, None)
        self.assertEqual(self.tika.valid_content_types, ["application/zip"])

    def test_setters(self):

        self.tika.jar = "jar"
        self.tika.valid_content_types = ["valid_content_types"]
        self.tika.memory_allocation = "512m"

        self.assertEqual(self.tika.jar, "jar")
        self.assertEqual(self.tika.memory_allocation, "512m")
        self.assertEqual(
            self.tika.valid_content_types, ["valid_content_types"])

        with self.assertRaises(sp.InvalidContentTypes):
            self.tika.valid_content_types = "application/zip"

    def test_missing_api_key(self):
        """Test MissingArgument exception."""

        with self.assertRaises(sp.MissingArgument):
            sp.TikaProcessing()


if __name__ == '__main__':
    unittest.main()
