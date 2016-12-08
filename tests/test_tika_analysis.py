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


class TestTikaAnalysis(unittest.TestCase):

    def test_meta_data(self):
        """Test meta data analysis."""

        # Parsing mail
        p = MailParser()
        p.parse_from_file(mail)

        # Init parameters
        new_attachments = []
        s = sp.SampleParser()
        t = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.14.jar",
            valid_content_types=[],
            memory_allocation=None)

        # Parsing sample
        for i in p.attachments_list:
            s.parse_sample_from_base64(
                data=i['payload'],
                filename=i['filename'],
                mail_content_type=i['mail_content_type'],
                transfer_encoding=i['content_transfer_encoding'])

            if s.result:
                new_attachments.append(s.result)

        # Tika analysis
        for i in new_attachments:
            t.process(i)
            self.assertNotIn('tika', i)

        t = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"],
            memory_allocation=None)

        for i in new_attachments:
            t.process(i)
            self.assertIn('tika', i)

    def test_invalid_attachments(self):
        """Test InvalidAttachments exception."""

        t = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"],
            memory_allocation=None)

        with self.assertRaises(sp.InvalidAttachment):
            t.process(["fake_attachment"])

    def test_properties(self):
        """Test properties output."""

        t = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"],
            memory_allocation=None)

        self.assertEqual(t.jar, "/opt/tika/tika-app-1.13.jar")
        self.assertEqual(t.memory_allocation, None)
        self.assertEqual(t.valid_content_types, ["application/zip"])

    def test_setters(self):
        t = sp.TikaProcessing(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=set(["application/zip"]),
            memory_allocation=None)

        t.jar = "jar"
        t.valid_content_types = ["valid_content_types"]
        t.memory_allocation = "512m"

        self.assertEqual(t.jar, "jar")
        self.assertEqual(t.memory_allocation, "512m")
        self.assertEqual(t.valid_content_types, ["valid_content_types"])

        with self.assertRaises(sp.InvalidContentTypes):
            t.valid_content_types = "application/zip"

    def test_missing_api_key(self):
        """Test MissingArgument exception."""

        with self.assertRaises(sp.MissingArgument):
            sp.TikaProcessing()


if __name__ == '__main__':
    unittest.main()
