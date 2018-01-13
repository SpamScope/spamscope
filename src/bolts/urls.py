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

from pyfaup.faup import Faup

from modules import AbstractBolt, load_whitelist, text2urls_whitelisted
from modules.attachments import MailAttachments


class Urls(AbstractBolt):
    outputs = ['sha256_random', 'results']

    def initialize(self, stormconf, context):
        super(Urls, self).initialize(stormconf, context)

        # Faup
        self.faup = Faup()

        # Input bolts for Phishing bolt
        self.input_bolts = set(context["source->stream->grouping"].keys())

        # All mails
        self._mails = {}

        # Load keywords
        self._load_lists()

    def _load_lists(self):

        # Load subjects keywords
        self.whitelists = load_whitelist(self.conf.get("whitelists", {}))
        self.log("Whitelists domains reloaded", "debug")

    def _get_urls(self, greedy_data):

        # If mail is filtered don't check for urls
        is_filtered = greedy_data["tokenizer"][2]
        results = {}

        # urls body
        if not is_filtered:
            text = greedy_data["tokenizer"][1]
            urls = text2urls_whitelisted(text, self.whitelists, self.faup)
            if urls:
                results["body"] = urls

        # I can have 2 mails with same body, but with different attachments
        attachments = MailAttachments(greedy_data["attachments"][2])
        text = attachments.payloadstext()
        urls = text2urls_whitelisted(text, self.whitelists, self.faup)
        if urls:
            results["attachments"] = urls

        return results

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """
        super(Urls, self).process_tick(freq)
        self._load_lists()

    def process(self, tup):
        bolt = tup.component
        sha256_random = tup.values[0]
        values = tup.values

        self._mails.setdefault(sha256_random, {})[bolt] = values
        diff = self.input_bolts - set(self._mails[sha256_random].keys())

        if not diff:
            results = self._get_urls(self._mails.pop(sha256_random))
            self.emit([sha256_random, results])
