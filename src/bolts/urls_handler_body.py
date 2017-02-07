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

from __future__ import absolute_import, print_function, unicode_literals
from modules import AbstractUrlsHandlerBolt


class UrlsHandlerBody(AbstractUrlsHandlerBolt):
    outputs = ['sha256_random', 'with_urls', 'urls']

    def process(self, tup):
        sha256_random = tup.values[0]
        body = tup.values[1]
        is_filtered = tup.values[2]
        with_urls = False
        urls_json = None

        if not is_filtered:
            with_urls, urls_json = self._extract_urls(body)

        self.emit([sha256_random, with_urls, urls_json])
