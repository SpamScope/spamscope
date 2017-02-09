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
sys.path.append(root)

import src.modules.bitmap as bitmap
from src.modules.bitmap import PhishingBitMap


class ValidBitMap(bitmap.BitMap):

    _map_name = "valid_bitmap"

    def define_bitmap(self):
        self._bitmap = {
            "property_0": 0,
            "property_1": 1,
            "property_2": 2,
        }


class InValidBitMap(bitmap.BitMap):

    _map_name = "invalid_bitmap"

    def define_bitmap(self):
        self._bitmap = {
            "property_0": 0,
            # "property_1": 1,
            "property_2": 2,
        }


class MissingBitMap(bitmap.BitMap):

    _map_name = "missing_bitmap"

    def define_bitmap(self):
        self._notbitmap = {
            "property_0": 0,
            "property_1": 1,
            "property_2": 2,
        }


class TestBitMap(unittest.TestCase):
    bm = ValidBitMap()

    def test_valid_map(self):
        self.assertRaises(
            bitmap.BitMapNotValid,
            InValidBitMap,
        )

    def test_missing_map(self):
        self.assertRaises(
            bitmap.BitMapNotDefined,
            MissingBitMap,
        )

    def test_reset_score(self):
        self.assertEqual(self.bm.score, 0)

        self.bm.reset_score()
        self.assertEqual(self.bm.score, 0)

        self.score = 0
        self.assertEqual(self.bm.score, 0)

    def test_score(self):
        with self.assertRaises(bitmap.ScoreOutOfRange):
            self.bm.score = 10

        self.assertEqual(self.bm.score, 0)

        self.bm.score = 4
        self.assertEqual(self.bm.score, 4)

    def test_map_name(self):
        self.assertEqual(self.bm.map_name, "valid_bitmap")

        self.bm.map_name = "new_bitmap"
        self.assertEqual(self.bm.map_name, "new_bitmap")

    def test_set_unset(self):
        self.bm.reset_score()

        self.bm.set_property_score('property_2')
        self.assertEqual(self.bm.score, 4)

        self.bm.unset_property_score('property_2')
        self.assertEqual(self.bm.score, 0)

        self.bm.set_property_score('property_0')
        self.bm.set_property_score('property_1')
        self.bm.set_property_score('property_2')
        self.assertEqual(self.bm.score, 7)

        self.bm.unset_property_score('property_0')
        self.assertEqual(self.bm.score, 6)

        self.bm.unset_property_score('property_1')
        self.assertEqual(self.bm.score, 4)

        self.bm.unset_property_score('property_2')
        self.assertEqual(self.bm.score, 0)

        self.bm.set_property_score(
            'property_0',
            'property_1',
            'property_2',
        )
        self.assertEqual(self.bm.score, 7)

        self.bm.unset_property_score(
            'property_0',
            'property_1',
            'property_2',
        )
        self.assertEqual(self.bm.score, 0)

        with self.assertRaises(bitmap.PropertyDoesNotExists):
            self.bm.set_property_score('property_fake')

        with self.assertRaises(bitmap.PropertyDoesNotExists):
            self.bm.unset_property_score('property_fake')

    def test_score_properties(self):
        self.bm.reset_score()

        self.assertEqual(self.bm.score_properties, [])

        self.assertIsInstance(self.bm.score_properties, list)

        self.bm.score = 7
        properties = ['property_2', 'property_1', 'property_0']
        self.assertEqual(self.bm.score_properties, properties)

    def test_calculate_score(self):
        self.bm.reset_score()

        score = self.bm.calculate_score(
            # 'property_0',
            'property_1',
            'property_2',
        )
        self.assertEqual(score, 6)

        with self.assertRaises(bitmap.PropertyDoesNotExists):
            self.bm.calculate_score(
                'property_fake',
            )

    def test_score_sum(self):
        self.bm.reset_score()

        score = self.bm.get_score_sum(2, 1, 0)
        self.assertEqual(score, 7)

    def test_phishing_bitmap(self):
        phishing_bitmap = PhishingBitMap()

        max_score = phishing_bitmap.calculate_score(
            "mail_body",
            "urls_body",
            "text_attachments",
            "urls_attachments",
            "filename_attachments",
            "mail_from",
            "mail_subject",
        )
        self.assertEqual(max_score, 127)


if __name__ == '__main__':
    unittest.main(verbosity=2)
