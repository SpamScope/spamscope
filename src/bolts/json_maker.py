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
from modules.bitmap import PhishingBitMap


def reformat_urls(urls):
    # Change urls format to fix Elasticsearch issue with dot '.'
    new_urls = []

    for v in urls.values():
        new_urls.extend(v)

    return new_urls


class JsonMaker(Bolt):
    outputs = ['sha256_random', 'json']

    def initialize(self, stormconf, context):
        self._mails = {}
        self.input_bolts = set(context["source->stream->grouping"].keys())

        # Phishing bitmap
        self._phishing_bitmap = PhishingBitMap()

    def _compose_output(self, greedy_data):

        # Tokenizer
        mail = greedy_data["tokenizer"][1]
        mail["is_filtered"] = greedy_data["tokenizer"][2]

        # Attachments
        # with_raw_attachments: the mail has attachments
        # with_attachments: the mail has not filtered attachments
        mail["with_raw_attachments"] = greedy_data["attachments"][1]
        attachments = greedy_data["attachments"][2]

        if attachments:
            mail["with_attachments"] = True
            mail["attachments"] = attachments
        else:
            mail["with_attachments"] = False

        # Urls in attachments:
        # Add urls attachments because you can have more differents attachments
        # in more mails with same hash
        mail["with_urls_attachments"] = \
            greedy_data["urls-handler-attachments"][1]

        if mail["with_urls_attachments"]:
            urls = greedy_data["urls-handler-attachments"][2]
            mail["urls_attachments"] = reformat_urls(urls)

        # Network
        network = greedy_data["network"][1]
        if network:
            mail["network"] = network

        # Add intelligence output only if mail is not filtered
        if not mail["is_filtered"]:

            # Phishing:
            # we need of a complete mail for a complete score, so
            # if mail is filtered we can't compose score
            phishing_score = greedy_data["phishing"][2]
            mail["with_phishing"] = greedy_data["phishing"][1]
            mail["phishing_score"] = phishing_score

            if phishing_score:
                self._phishing_bitmap.score = phishing_score
                mail["targets"] = greedy_data["phishing"][3]
                mail["phishing_score_expanded"] = \
                    self._phishing_bitmap.score_properties

            # Forms
            mail["with_forms"] = greedy_data["forms"][1]

            # Urls in body
            mail["with_urls_body"] = greedy_data["urls-handler-body"][1]

            if mail["with_urls_body"]:
                urls = greedy_data["urls-handler-body"][2]
                mail["urls_body"] = reformat_urls(urls)

        return mail

    def process(self, tup):
        bolt = tup.component
        sha256_random = tup.values[0]
        values = tup.values

        self._mails.setdefault(sha256_random, {})[bolt] = values
        diff = self.input_bolts - set(self._mails[sha256_random].keys())

        if not diff:
            output_json = self._compose_output(self._mails.pop(sha256_random))
            self.log("New JSON for mail {!r}".format(sha256_random), "debug")
            self.emit([sha256_random, output_json])
