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
from modules import reformat_urls


class JsonMaker(Bolt):
    outputs = ['sha256_random', 'json']

    def initialize(self, stormconf, context):
        self._mails = {}
        self.input_bolts = set(context["source->stream->grouping"].keys())

    def _compose_output(self, greedy_data):

        # # # Tokenizer # # #
        mail = greedy_data["tokenizer"][1]
        mail["is_filtered"] = greedy_data["tokenizer"][2]

        # # # Attachments # # #
        # with_attachments: the mail has raw attachments
        mail["with_attachments"] = greedy_data["attachments"][1]
        attachments = greedy_data["attachments"][2]
        if attachments:
            mail["attachments"] = attachments

        # # # Urls # # #
        urls_body = greedy_data["urls"][1].get("body", {})
        urls_attachments = greedy_data["urls"][1].get("attachments", {})

        if urls_body:
            mail.setdefault("urls", {}).update(
                {"body": reformat_urls(urls_body)})

        if urls_attachments:
            mail.setdefault("urls", {}).update(
                {"attachments": reformat_urls(urls_attachments)})

        # # # Network # # #
        network = greedy_data["network"][1]
        mail["network"] = {"is_filtered": greedy_data["network"][2]}
        if network:
            mail["network"].update(network)

        # # # Raw mail # # #
        raw_mail = greedy_data["raw_mail"][1]
        mail["raw_mail"] = {"is_filtered": greedy_data["raw_mail"][2]}
        if raw_mail:
            mail["raw_mail"].update(raw_mail)

        # # # Phishing # # #
        phishing = greedy_data["phishing"][1]
        if phishing:
            mail["phishing"] = phishing

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
