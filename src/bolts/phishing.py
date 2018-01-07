#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

from modules import AbstractBolt, load_keywords_list, load_keywords_dict
from modules.mails import check_phishing


class Phishing(AbstractBolt):
    outputs = ['sha256_random', 'results']

    def initialize(self, stormconf, context):
        super(Phishing, self).initialize(stormconf, context)

        # Input bolts for Phishing bolt
        self.input_bolts = set(context["source->stream->grouping"].keys())

        # All mails
        self._mails = {}

        # Load keywords
        self._load_lists()

    def _load_lists(self):

        # Load subjects keywords
        self.subject_keys = load_keywords_list(
            self.conf["lists"].get("subjects", {}))
        self.log("Phishing subjects keywords reloaded", "debug")

        # Load targets keywords
        self.target_keys = load_keywords_dict(
            self.conf["lists"].get("targets", {}))
        self.log("Phishing targets keywords reloaded", "debug")

    def _phishing(self, greedy_data):

        # If mail is filtered don't check for phishing
        is_filtered = greedy_data["tokenizer"][2]
        results = {}

        if not is_filtered:

            # Get all data
            email = greedy_data["tokenizer"][1]
            attachments = greedy_data["attachments"][2]
            urls_body = greedy_data["urls"][1].get("body", {})
            urls_attachments = greedy_data["urls"][1].get("attachments", {})

            results = check_phishing(
                email=email,
                attachments=attachments,
                urls_body=urls_body,
                urls_attachments=urls_attachments,
                target_keys=self.target_keys,
                subject_keys=self.subject_keys)

        return results

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """
        super(Phishing, self).process_tick(freq)
        self._load_lists()

    def process(self, tup):
        bolt = tup.component
        sha256_random = tup.values[0]
        values = tup.values

        self._mails.setdefault(sha256_random, {})[bolt] = values
        diff = self.input_bolts - set(self._mails[sha256_random].keys())

        if not diff:
            results = self._phishing(
                self._mails.pop(sha256_random))

            self.emit([sha256_random, results])
