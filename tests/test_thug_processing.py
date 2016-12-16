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
mail = os.path.join(base_path, 'samples', 'mail_thug')
sys.path.append(root)
import src.modules.sample_parser as sp


class TestThugProcessing(unittest.TestCase):

    def setUp(self):

        # Init
        p = MailParser()
        s = sp.SampleParser()
        self.thug = sp.ThugProcessing(
            referer="http://www.google.com/",
            extensions=[".js"],
            user_agents=["win7ie90", "winxpie80"])

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

    def test_result(self):
        # First mail attachment
        first_attachment = self.attachments[0]

        # Thug processing
        self.thug.process(first_attachment)
        self.assertNotIn('thug', first_attachment)

        # Attachment
        thug_attachment = first_attachment['files'][0]
        self.assertIn('thug', thug_attachment)

        thug_analysis = thug_attachment['thug']
        self.assertIsInstance(thug_analysis, list)
        self.assertEqual(len(thug_analysis), 2)

        first_thug_analysis = thug_analysis[0]
        # ['files', 'code', 'exploits', 'url', 'timestamp', 'locations',
        # 'connections', 'logtype', 'behavior', 'thug', 'classifiers']
        self.assertIn('files', first_thug_analysis)
        self.assertIn('code', first_thug_analysis)
        self.assertIn('exploits', first_thug_analysis)
        self.assertIn('url', first_thug_analysis)
        self.assertIn('timestamp', first_thug_analysis)
        self.assertIn('locations', first_thug_analysis)
        self.assertIn('connections', first_thug_analysis)
        self.assertIn('logtype', first_thug_analysis)
        self.assertIn('behavior', first_thug_analysis)
        self.assertIn('thug', first_thug_analysis)
        self.assertIn('classifiers', first_thug_analysis)
        self.assertEqual(first_thug_analysis['files'][0]['sha1'],
                         "e2835a38f50d287c65b0e53b4787d41095a3514f")
        self.assertEqual(first_thug_analysis['files'][0]['md5'],
                         "b83c7ac97c22ce248b09f4388c130df0")
        self.assertEqual(
            first_thug_analysis['thug']['personality']['useragent'],
            'win7ie90')
        self.assertEqual(
            first_thug_analysis['thug']['options']['referer'],
            'http://www.google.com/')

    def test_invalid_attachments(self):
        """Test InvalidAttachments exception."""

        with self.assertRaises(sp.InvalidAttachment):
            self.thug.process([])

    def test_missing_args(self):

        with self.assertRaises(sp.MissingArgument):
            sp.ThugProcessing(referer="test", extensions=[])

        with self.assertRaises(sp.MissingArgument):
            sp.ThugProcessing(referer="test", user_agents=[])

        with self.assertRaises(sp.MissingArgument):
            sp.ThugProcessing(user_agents="test", extensions=[])


if __name__ == '__main__':
    unittest.main()
