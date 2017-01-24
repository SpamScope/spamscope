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
from src.modules.attachments import MailAttachments


class TestAttachments(unittest.TestCase):

    def setUp(self):
        # Init
        p = MailParser()
        p.parse_from_file(mail)
        self.attachments = p.attachments_list

    def test_withhashes(self):
        t = MailAttachments.withhashes(self.attachments)
        self.assertIsInstance(t, MailAttachments)
        self.assertEqual(len(t), 1)

        for i in t:
            self.assertIn("md5", i)
            self.assertIn("sha1", i)
            self.assertIn("sha256", i)
            self.assertIn("sha512", i)
            self.assertIn("ssdeep", i)
            self.assertIn("filename", i)
            self.assertIn("payload", i)
            self.assertIn("mail_content_type", i)
            self.assertIn("content_transfer_encoding", i)

        t.pophash("1e38e543279912d98cbfdc7b275a415e")
        self.assertEqual(len(t), 0)

    def test_run(self):
        dummy = {"key1": "value1", "key2": "value2"}
        t = MailAttachments.withhashes(self.attachments)
        t(**dummy)
        for i in t:
            i.pop("payload")
            for j in i.get("files", []):
                j.pop("payload")

        print t


if __name__ == '__main__':
    unittest.main()
