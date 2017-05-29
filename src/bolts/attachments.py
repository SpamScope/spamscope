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
import copy
from modules import AbstractBolt, load_keywords_list
from modules.attachments import MailAttachments
from binascii import Error


class Attachments(AbstractBolt):
    outputs = ['sha256_random', 'with_attachments', 'attachments']

    def initialize(self, stormconf, context):
        super(Attachments, self).initialize(stormconf, context)
        self.attach = MailAttachments()
        self._load_settings()

    def _load_settings(self):
        # Loading configuration
        self._load_lists()

        settings = copy.deepcopy(self.conf)
        settings.update(
            {"filter_cont_types": self._filter_cont_types,
             "tika_whitelist_cont_types": self._tika_whitelist_cont_types})

        self.attach.reload(**settings)

    def _load_lists(self):

        # Load content types to filter
        self._filter_cont_types = load_keywords_list(
            self.conf["content_types_blacklist"], lower=False)
        self.log("Content types to filter reloaded")

        # Load Tika content types to analyze
        self._tika_whitelist_cont_types = set()
        if self.conf["tika"]["enabled"]:
            self._tika_whitelist_cont_types = load_keywords_list(
                self.conf["tika"]["valid_content_types"], lower=False)
            self.log("Whitelist Tika content types reloaded")

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """
        super(Attachments, self).process_tick(freq)
        self._load_settings()

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            with_attachments = tup.values[1]

            # Remove all values
            self.attach.removeall()

            # Add the new values
            self.attach.extend(tup.values[2])

            # Run analysis
            # self.attach.run() == self.attach()
            self.attach.run()

        except Error, e:
            self.raise_exception(e, tup)

        else:
            # emit
            self.emit([sha256_random, with_attachments, list(self.attach)])
