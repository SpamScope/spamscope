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

API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


class TestVirusTotalProcessing(unittest.TestCase):

    def test_process(self):
        """Test add VirusTotal analysis."""

        # Parsing mail
        p = MailParser()
        p.parse_from_file(mail)

        # Init parameters
        new_attachments = []
        s = sp.SampleParser()
        v = sp.VirusTotalProcessing(api_key=API_KEY)

        # Parsing sample
        for i in p.attachments_list:
            s.parse_sample_from_base64(
                data=i['payload'],
                filename=i['filename'],
                mail_content_type=i['mail_content_type'],
                transfer_encoding=i['content_transfer_encoding'])

            if s.result:
                new_attachments.append(s.result)

        # VirusTotal analysis
        for i in new_attachments:
            v.process(i)
            self.assertIn('virustotal', i)

            for j in i["files"]:
                self.assertIn('virustotal', j)

    def test_invalid_attachments(self):
        """Test InvalidAttachments exception."""

        v = sp.VirusTotalProcessing(api_key=API_KEY)

        with self.assertRaises(sp.InvalidAttachment):
            v.process([])

    def test_invalid_api_key(self):
        """Test VirusTotalApiKeyInvalid exception."""

        with self.assertRaises(sp.VirusTotalApiKeyInvalid):
            sp.VirusTotalProcessing(api_key=None)

    def test_missing_api_key(self):
        """Test MissingArgument exception."""

        with self.assertRaises(sp.MissingArgument):
            sp.VirusTotalProcessing()


if __name__ == '__main__':
    unittest.main()
