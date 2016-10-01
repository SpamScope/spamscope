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
        t = sp.TikaAnalysis(
            jar="/opt/tika/tika-app-1.13.jar")

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
            t.add_meta_data(i)
            self.assertNotIn('tika', i)

        t = sp.TikaAnalysis(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"])

        for i in new_attachments:
            t.add_meta_data(i)
            self.assertIn('tika', i)

    def test_invalid_attachments(self):
        """Test InvalidAttachments exception."""

        t = sp.TikaAnalysis(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"])

        with self.assertRaises(sp.InvalidAttachment):
            t.add_meta_data(["fake_attachment"])

    def test_properties(self):
        """Test properties output."""

        t = sp.TikaAnalysis(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"])

        self.assertEqual(t.jar, "/opt/tika/tika-app-1.13.jar")
        self.assertEqual(t.memory_allocation, None)
        self.assertEqual(t.valid_content_types, ["application/zip"])

    def test_setters(self):
        t = sp.TikaAnalysis(
            jar="/opt/tika/tika-app-1.13.jar",
            valid_content_types=["application/zip"])

        t.jar = "test1"
        t.valid_content_types = set(["test2"])

        self.assertEqual(t.jar, "test1")
        self.assertEqual(t.memory_allocation, None)
        self.assertEqual(t.valid_content_types, set(["test2"]))

        with self.assertRaises(sp.InvalidContentTypes):
            t.valid_content_types = ["application/zip"]

if __name__ == '__main__':
    unittest.main()
