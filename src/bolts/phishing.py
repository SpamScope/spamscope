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
from bolts.abstracts import AbstractBolt

try:
    import simplejson as json
except ImportError:
    import json

from modules.phishing_bitmap import PhishingBitMap


class Phishing(AbstractBolt):

    def initialize(self, stormconf, context):
        super(Phishing, self).initialize(stormconf, context)

        # Input bolts for Phishing bolt
        self.input_bolts = set(
            [
                "tokenizer-bolt",
                "attachments-bolt",
                "urls_handler_body-bolt",
            ]
        )

        # All mails
        self.mails = {}

        # Load key words
        self._load_generic_keywords()
        self._load_subject_keywords()

        # Phishing bitmap
        self._phishing_bitmap = PhishingBitMap()

    def _load_generic_keywords(self):
        pass

    def _load_subject_keywords(self):
        pass

    def _search_phishing(self, greedy_data):
        # Reset phishing bitmap
        self._phishing_bitmap.reset_score()

        # Tokenizer
        mail = json.loads(greedy_data['tokenizer-bolt'][1])
        body = mail.get('body')
        subject = mail.get('subject')
        from_ = mail.get('from')

        # Check body
        if body:
            pass

        # Check subject
        if subject:
            pass

        # Check from mail
        if from_:
            pass

        # Attachments
        with_attachments = greedy_data['attachments-bolt'][1]
        if with_attachments:
            # TODO: if tika
            pass

        # Urls in body
        with_urls_body = greedy_data['urls_handler_body-bolt'][1]
        if with_urls_body:
            pass

        return self._phishing_bitmap.score

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """

        self._load_generic_keywords()
        self._load_subject_keywords()

    def process(self, tup):
        try:
            bolt = tup.component
            sha256_random = tup.values[0]
            values = tup.values

            if self.mails.get(sha256_random, None):
                self.mails[sha256_random][bolt] = values
            else:
                self.mails[sha256_random] = {bolt: values}

            diff = self.input_bolts - set(self.mails[sha256_random].keys())
            if not diff:
                with_phishing = False
                score = self._search_phishing(
                    self.mails.pop(sha256_random)
                )
                if score:
                    with_phishing = True

                self.emit([sha256_random, with_phishing, score])

        except Exception as e:
            self.log(
                "Failed processing phishing for mail '{}".format(
                    sha256_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)
