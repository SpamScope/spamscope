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
from modules import AbstractBolt
from modules.networks import processors


class Network(AbstractBolt):
    outputs = ['sha256_random', 'network', 'is_filtered']

    def process(self, tup):
        sha256_random = tup.values[0]
        ipaddress = tup.values[1]
        is_filtered = tup.values[2]

        try:
            results = {}

            if not is_filtered:
                for p in processors:
                    try:
                        p(self.conf[p.__name__], ipaddress, results)
                    except KeyError:
                        self.log("KeyError: {!r} doesn't exist in conf".format(
                            p.__name__), "error")

        except Exception as e:
            self.log("Failed process network for mail: {}".format(
                sha256_random), "error")
            self.raise_exception(e, tup)

        else:
            self.emit([sha256_random, results])
