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
from modules.errors import ImproperlyConfigured
from modules.utils import \
    search_words_in_text, \
    load_config


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

        # Load keywords
        self._load_lists()

        # Phishing bitmap
        self._phishing_bitmap = PhishingBitMap()

    def _load_lists(self):

        self.log("Reloading phishing keywords")

        # Load subjects keywords
        self._subjects_keywords = set()
        for k, v in self.conf["lists"]["subjects"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, list):
                raise ImproperlyConfigured(
                    "Keywords subjects list '{}' not valid".format(v)
                )
            self._subjects_keywords |= set(keywords)

        # Load targets keywords
        self._targets_keywords = {}
        for k, v in self.conf["lists"]["targets"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, dict):
                raise ImproperlyConfigured(
                    "Keywords targets list '{}' not valid".format(v)
                )
            self._targets_keywords.update(keywords)

    def _search_phishing(self, greedy_data):
        # Reset phishing bitmap
        self._phishing_bitmap.reset_score()

        # Outputs
        targets = set()

        # Tokenizer
        mail = json.loads(greedy_data['tokenizer-bolt'][1])
        body = mail.get('body')
        subject = mail.get('subject')
        from_ = mail.get('from')

        body_match = False
        from_match = False
        subject_match = False

        # Check body and from
        for k, v in self._targets_keywords.iteritems():
            if body:
                if search_words_in_text(body, v):
                    targets.add(k)
                    body_match = True

            if from_:
                if search_words_in_text(from_, v):
                    targets.add(k)
                    from_match = True

        # Check subject
        if search_words_in_text(
            subject,
            self._subjects_keywords,
        ):
            subject_match = True

        # Attachments
        with_attachments = greedy_data['attachments-bolt'][1]
        if with_attachments:
            # TODO: if tika
            pass

        # Urls in body
        with_urls_body = greedy_data['urls_handler_body-bolt'][1]
        if with_urls_body:
            pass

        # Setting score
        if body_match:
            self._phishing_bitmap.set_property_score("mail_body")

        if from_match:
            self._phishing_bitmap.set_property_score("mail_from")

        if subject_match:
            self._phishing_bitmap.set_property_score("mail_subject")

        return self._phishing_bitmap.score, targets

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """

        self._load_lists()

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
                score, targets = self._search_phishing(
                    self.mails.pop(sha256_random)
                )
                if score:
                    with_phishing = True

                targets = json.dumps(
                    list(targets),
                    ensure_ascii=False,
                )

                self.emit([sha256_random, with_phishing, score, targets])

        except Exception as e:
            self.log(
                "Failed processing phishing for mail '{}".format(
                    sha256_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)
