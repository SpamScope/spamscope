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

file_js = os.path.join(base_path, 'sample', 'snippet_javascript.js')

from src.modules.thug_analysis import ThugAnalysis


class TestThugAnalysis(unittest.TestCase):
    thug_analyzer = ThugAnalysis()
    results = thug_analyzer.analyze()

    def test_result(self):
        pass


if __name__ == '__main__':
    unittest.main()
