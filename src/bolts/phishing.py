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
from functools import partial
from modules import (AbstractBolt, load_keywords_list, load_keywords_dict,
                     search_words_in_text as swt, search_words_given_key)
from modules.attachments import MailAttachments
from modules.bitmap import PhishingBitMap


def check_urls(urls, keywords):
    for domain, details in urls.iteritems():
        for i in details:
            if swt(i["url"], keywords):
                return True
    return False


class Phishing(AbstractBolt):
    outputs = ['sha256_random', 'with_phishing', 'score', 'targets']

    def initialize(self, stormconf, context):
        super(Phishing, self).initialize(stormconf, context)

        # Input bolts for Phishing bolt
        self.input_bolts = set(context["source->stream->grouping"].keys())

        # Phishing bitmap
        self._pb = PhishingBitMap()

        # All mails
        self._mails = {}

        # Load keywords
        self._load_lists()

    def _load_lists(self):

        # Load subjects keywords
        self._s_keys = load_keywords_list(self.conf["lists"]["subjects"])
        self.log("Phishing subjects keywords reloaded")

        # Load targets keywords
        self._t_keys = load_keywords_dict(self.conf["lists"]["targets"])
        self.log("Phishing targets keywords reloaded")

    def _search_phishing(self, greedy_data):
        with_urls = False

        # If mail is filtered don't check for phishing
        is_filtered = greedy_data["tokenizer"][2]

        if is_filtered:
            return False, False, False

        # Reset phishing bitmap
        self._pb.reset_score()

        # Outputs
        targets = set()

        # Get all data
        mail = greedy_data["tokenizer"][1]
        body = mail.get('body')
        subject = mail.get('subject')
        from_ = mail.get('from')
        urls_body = greedy_data["urls-handler-body"][2]
        urls_attachments = greedy_data["urls-handler-attachments"][2]

        # TODO: if an attachment is filtered, the score is not complete
        # more different mails can have the same attachment
        # more different attachments can have the same mail
        attachments = MailAttachments(greedy_data["attachments"][2])

        urls = (
            (urls_body, 'urls_body'),
            (urls_attachments, 'urls_attachments'))

        # Mapping for targets checks
        mapping_targets = (
            (body, 'mail_body'),
            (from_, 'mail_from'),
            (attachments.payloadstext(), 'text_attachments'),
            (attachments.filenamestext(), 'filename_attachments'))

        for k, v in mapping_targets:
            if k:
                matcher = partial(search_words_given_key, k)
                t = set(i for i in map(matcher, self._t_keys.iteritems()) if i)
                if t:
                    targets |= t
                    self._pb.set_property_score(v)

        # Check urls
        # Target not added because text urls already analyzed
        for k, v in urls:
            if k:
                with_urls = True
                if any(check_urls(k, i) for i in self._t_keys.values()):
                    self._pb.set_property_score(v)

        # Check subject
        if swt(subject, self._s_keys):
            self._pb.set_property_score("mail_subject")

        return self._pb.score, list(targets), with_urls

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
            with_phishing = False

            score, targets, with_urls = self._search_phishing(
                self._mails.pop(sha256_random))

            # There is phishing only if there is also urls
            # Mail can have target without phishing
            if score and with_urls:
                with_phishing = True
            else:
                with_phishing = False
                score = 0

            self.emit([sha256_random, with_phishing, score, targets])
