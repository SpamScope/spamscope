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

import src.modules.utils as utils

text_files = os.path.join(base_path, 'samples', 'lorem_ipsum.txt')


class TestSearchText(unittest.TestCase):

    def test_check_text(self):
        with open(text_files) as f:
            text = f.read()

        keywords_1 = [
            "nomatch",
            "nomatch",
        ]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_1),
            False
        )

        keywords_2 = [
            "nomatch",
            "nomatch",
            "theophrastus rationibus"
        ]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2),
            True
        )

        keywords_2 = [
            "nomatch",
            "theophrastus nomatch",
        ]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2),
            False
        )

        keywords_2 = [
            "theophrastus quo vidit",
        ]

        self.assertEqual(
            utils.search_words_in_text(text, keywords_2),
            True
        )


if __name__ == '__main__':
    unittest.main()
