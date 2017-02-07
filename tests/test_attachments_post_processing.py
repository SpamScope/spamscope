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
from src.modules.attachments import (MailAttachments, virustotal, tika)

API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"


class TestPostProcessing(unittest.TestCase):

    def setUp(self):

        # Init
        p = MailParser()
        p.parse_from_file(mail)
        self.attachments = p.attachments_list

    def test_virustotal(self):
        """Test add VirusTotal processing."""

        conf = {"enabled": True, "api_key": API_KEY}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        virustotal(conf, attachments)

        # VirusTotal analysis
        for i in attachments:
            self.assertIn('virustotal', i)
            self.assertEqual(i['virustotal']['response_code'], 200)
            self.assertEqual(i['virustotal']['results']['sha1'],
                             '2a7cee8c214ac76ba6fdbc3031e73dbede95b803')

            for j in i["files"]:
                self.assertIn('virustotal', j)
                self.assertEqual(j['virustotal']['response_code'], 200)
                self.assertEqual(j['virustotal']['results']['sha1'],
                                 'ed2e480e7ba7e37f77a85efbca4058d8c5f92664')

    def test_tika(self):
        """Test add Tika processing."""

        # Complete parameters
        conf = {"enabled": True,
                "path_jar": "/opt/tika/tika-app-1.14.jar",
                "memory_allocation": None,
                "whitelist_cont_types": ["application/zip"]}
        attachments = MailAttachments.withhashes(self.attachments)
        attachments(intelligence=False)
        tika(conf, attachments)

        for i in attachments:
            self.assertIn("tika", i)

        self.assertEqual(len(attachments[0]["tika"]), 2)
        self.assertEqual(
            int(attachments[0]["tika"][0]["Content-Length"]),
            attachments[0]["size"])

        # tika disabled
        conf["enabled"] = False
        attachments = MailAttachments.withhashes(self.attachments)
        attachments()
        tika(conf, attachments)

        for i in attachments:
            self.assertNotIn("tika", i)

        conf["enabled"] = True

        # attachments without run()
        with self.assertRaises(KeyError):
            attachments = MailAttachments.withhashes(self.attachments)
            tika(conf, attachments)

        # attachments a key of conf
        with self.assertRaises(KeyError):
            conf_inner = {"enabled": True,
                          "path_jar": "/opt/tika/tika-app-1.14.jar",
                          "memory_allocation": None}
            attachments = MailAttachments.withhashes(self.attachments)
            tika(conf_inner, attachments)


if __name__ == '__main__':
    unittest.main()
