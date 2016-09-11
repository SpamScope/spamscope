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
import tikapp as tika

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sample_zip = os.path.join(base_path, 'samples', 'test.zip')
sample_zip_1 = os.path.join(base_path, 'samples', 'test1.zip')
sample_txt = os.path.join(base_path, 'samples', 'test.txt')
sys.path.append(root)
import src.modules.sample_parser as sample_parser


class TestSampleParser(unittest.TestCase):

    def test_is_archive(self):
        """Test is_archive functions."""

        parser = sample_parser.SampleParser()

        with open(sample_zip, 'rb') as f:
            data = f.read()
            data_base64 = data.encode('base64')

        sha1_archive = "8760ff1422cf2922b649b796cfb58bfb0ccf7801"

        # Test is_archive with write_sample=False
        result1 = parser.is_archive(data)
        self.assertEqual(True, result1)

        result2 = parser.is_archive_from_base64(data_base64)
        self.assertEqual(True, result2)

        self.assertEqual(result1, result2)

        # Test is_archive with write_sample=True
        result = parser.is_archive(data, write_sample=True)
        self.assertEqual(os.path.exists(result[1]), True)

        # Sample on disk
        with open(result[1], 'rb') as f:
            data_new = f.read()

        result = parser.fingerprints(data_new)
        self.assertEqual(sha1_archive, result[1])

        result = parser.is_archive_from_base64(
            data_base64,
            write_sample=True
        )
        self.assertEqual(True, result[0])
        self.assertEqual(os.path.exists(result[1]), True)

        # Test is_archive with write_sample=True
        result = parser.is_archive(data, write_sample=True)
        self.assertIsInstance(result, tuple)

    def test_fingerprints(self):
        """Test fingerprints functions."""

        parser = sample_parser.SampleParser()

        with open(sample_zip, 'rb') as f:
            data = f.read()
            data_base64 = data.encode('base64')

        sha1_archive = "8760ff1422cf2922b649b796cfb58bfb0ccf7801"

        # Test fingerprints
        result1 = parser.fingerprints(data)[1]
        self.assertEqual(sha1_archive, result1)

        result2 = parser.fingerprints_from_base64(data_base64)[1]
        self.assertEqual(sha1_archive, result2)

        self.assertEqual(result1, result2)

    def test_parser_sample(self):
        """Test for parse_sample."""

        parser = sample_parser.SampleParser()

        with open(sample_zip, 'rb') as f:
            data = f.read()

        with open(sample_txt, 'rb') as f:
            data_txt_base64 = f.read().encode('base64')

        parser.parse_sample(data, "test.zip")
        result = parser.result

        md5_file = "d41d8cd98f00b204e9800998ecf8427e"
        size_file = 0
        size_zip = 166

        self.assertIsInstance(result, dict)
        self.assertEqual(result['size'], size_zip)
        self.assertIsNotNone(result['files'])
        self.assertIsInstance(result['files'], list)
        self.assertEqual(len(result['files']), 1)
        self.assertEqual(result['files'][0]['size'], size_file)
        self.assertEqual(result['files'][0]['md5'], md5_file)
        self.assertEqual(result['files'][0]['filename'], "test.txt")
        self.assertEqual(result['files'][0]['payload'], data_txt_base64)

    def test_blacklist_content_types(self):
        with open(sample_zip_1, 'rb') as f:
            data = f.read()

        # Blacklist for application/zip
        parser = sample_parser.SampleParser(
            tika_enabled=True,
            tika_jar="/opt/tika/tika-app-1.12.jar",
            tika_content_types=[],
            blacklist_content_types=["application/zip"],
        )

        parser.parse_sample(data, "test1.zip")
        result = parser.result
        self.assertEqual(result, None)

    def test_payload_content_filename(self):
        with open(sample_zip_1, 'rb') as f:
            data = f.read()

        # Blacklist for application/zip
        parser = sample_parser.SampleParser(
            tika_enabled=True,
            tika_jar="/opt/tika/tika-app-1.12.jar",
            tika_content_types=[],
            blacklist_content_types=[],
        )

        parser.parse_sample(data, "test1.zip")
        result = parser.result

        self.assertIn("is_archive", result)
        all_contents = u""
        all_filenames = u""

        all_contents += result["files"][0]["payload"].decode("base64")
        self.assertIn("google", all_contents)
        self.assertIn("test1", all_contents)
        self.assertIn("http", all_contents)

        all_filenames += result["filename"] + u"\n"
        all_filenames += result["files"][0]["filename"] + u"\n"
        self.assertIn("test1.zip", all_filenames)
        self.assertIn("test1.txt", all_filenames)

    def test_add_tika(self):

        with self.assertRaises(tika.InvalidTikaAppJar):
            sample_parser.SampleParser(
                tika_enabled=True
            )

        # Only content type
        parser = sample_parser.SampleParser(
            tika_enabled=True,
            tika_jar="/opt/tika/tika-app-1.12.jar",
            tika_content_types=[],
            blacklist_content_types=[],
        )

        with open(sample_zip_1, 'rb') as f:
            data = f.read()

        sha1_sample_zip_1 = "8c1b27ef89963a935730d97de1b06dff9aa0f354"
        sha1_sample_txt_1 = "3e43e0eae28e9ca457098291621957e14ad7477a"

        parser.parse_sample(data, "test1.zip")
        result = parser.result

        self.assertEqual(sha1_sample_zip_1, result['sha1'])
        self.assertEqual(sha1_sample_txt_1, result['files'][0]['sha1'])
        self.assertNotIn('tika', result)
        self.assertEqual(result['Content-Type'], "application/zip")
        self.assertEqual(result['files'][0]['Content-Type'], "text/plain")

        # Tika process for application/zip
        parser = sample_parser.SampleParser(
            tika_enabled=True,
            tika_jar="/opt/tika/tika-app-1.12.jar",
            tika_content_types=["application/zip"],
            blacklist_content_types=[],
        )

        parser.parse_sample(data, "test1.zip")
        result = parser.result

        for i in result['tika']:
            self.assertIn('X-TIKA:content', i)
            self.assertIsInstance(i, dict)

        self.assertIn('test1.txt', result['tika'][0]['X-TIKA:content'])
        self.assertIn('google', result['tika'][1]['X-TIKA:content'])


if __name__ == '__main__':
    unittest.main()
