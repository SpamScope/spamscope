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
from streamparse.bolt import Bolt
from lxml import html
from lxml.etree import ParserError


class Forms(Bolt):
    outputs = ['sha256_random', 'with_form']

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            body = tup.values[1]
            is_filtered = tup.values[2]
            with_form = False

            if not is_filtered and body.strip():
                tree = html.fromstring(body)
                results = tree.xpath('//form')
                if results:
                    with_form = True
                    self.log("Forms for mail {!r}".format(sha256_random))

        except ParserError, e:
            self.raise_exception(e, tup)

        else:
            self.emit([sha256_random, with_form])
