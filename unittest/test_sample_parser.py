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

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sample_zip = os.path.join(root, 'unittest', 'samples', 'test.zip')
sys.path.append(root)
import src.modules.sample_parser as sample_parser


class TestSampleParser(unittest.TestCase):
    parser = sample_parser.SampleParser()

    def test_fingerprints_invalid_base64(self):
        self.assertRaises(
            sample_parser.Base64Error,
            self.parser.fingerprints_from_base64,
            "\test"
        )

    def test_parsing_know_values(self):
        with open(sample_zip, 'rb') as f:
            data = f.read()
            data_base64 = data.encode('base64')

        sha1 = "8760ff1422cf2922b649b796cfb58bfb0ccf7801"

        result1 = self.parser.is_archive(data)
        self.assertEqual(True, result1)

        result2 = self.parser.is_archive_from_base64(data_base64)
        self.assertEqual(True, result2)

        self.assertEqual(result1, result2)

        result1 = self.parser.fingerprints(data)[1]
        self.assertEqual(sha1, result1)

        result2 = self.parser.fingerprints_from_base64(data_base64)[1]
        self.assertEqual(sha1, result2)

        self.assertEqual(result1, result2)


if __name__ == '__main__':
    unittest.main()
