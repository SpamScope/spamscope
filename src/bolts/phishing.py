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
    search_words_in_text as swt, \
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
                "urls_handler_attachments-bolt",
            ]
        )

        # All mails
        self.mails = {}

        # Load keywords
        self._load_lists()

        # Phishing bitmap
        self._pb = PhishingBitMap()

    def _load_lists(self):

        self.log("Reloading phishing keywords")

        # Load subjects keywords
        self._s_keys = set()
        for k, v in self.conf["lists"]["subjects"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, list):
                raise ImproperlyConfigured(
                    "Keywords subjects list '{}' not valid".format(k)
                )
            self._s_keys |= set(keywords)

        # Load targets keywords
        self._t_keys = {}
        for k, v in self.conf["lists"]["targets"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, dict):
                raise ImproperlyConfigured(
                    "Keywords targets dict '{}' not valid".format(k)
                )
            self._t_keys.update(keywords)

    def _check_urls(self, urls, keywords):
        for domain, details in urls.iteritems():
            for i in details:
                if swt(i['url'], keywords):
                    return True

    def _check_attachments(self, attachments, keywords):
        all_filenames = ""
        all_contents = ""

        for i in attachments:
            all_filenames += i["filename"] + "\n"

            if i.get("is_archive"):
                for j in i.get("files"):
                    all_filenames += j["filename"] + "\n"
                    all_contents += j["payload"].decode('base64') + "\n"
            else:
                all_contents += i["payload"].decode('base64') + "\n"

        return swt(all_filenames, keywords), swt(all_contents, keywords)

    def _search_phishing(self, greedy_data):

        # Reset phishing bitmap
        self._pb.reset_score()

        # Outputs
        targets = set()

        # Get Tokenizer
        mail = json.loads(greedy_data['tokenizer-bolt'][1])
        body = mail.get('body')
        subject = mail.get('subject')
        from_ = mail.get('from')

        # Get Urls in body
        with_urls_body = greedy_data['urls_handler_body-bolt'][1]
        urls = None
        if with_urls_body:
            urls = json.loads(
                greedy_data['urls_handler_body-bolt'][2]
            )

        # Get Urls attachments
        with_urls_attachments = greedy_data['urls_handler_attachments-bolt'][1]
        urls_attachments = None
        if with_urls_attachments:
            urls_attachments = json.loads(
                greedy_data['urls_handler_attachments-bolt'][2]
            )

        # Get Attachments
        with_attachments = greedy_data['attachments-bolt'][1]
        attachments = None
        if with_attachments:
            attachments = json.loads(
                greedy_data['attachments-bolt'][2]
            )

        # Check body
        if body:
            for k, v in self._t_keys.iteritems():
                if swt(body, v):
                    targets.add(k)
                    if 'mail_body' not in self._pb.score_properties:
                        self._pb.set_property_score("mail_body")

        # Check urls body
        # Target not added because urls come from body
        if urls:
            for k, v in self._t_keys.iteritems():
                if 'urls_body' not in self._pb.score_properties:
                    if self._check_urls(urls, v):
                        self._pb.set_property_score("urls_body")

        # Check from
        if from_:
            for k, v in self._t_keys.iteritems():
                if swt(from_, v):
                    targets.add(k)
                    if 'mail_from' not in self._pb.score_properties:
                        self._pb.set_property_score("mail_from")

        # Check attachments filename and text match
        if with_attachments:
            for k, v in self._t_keys.iteritems():
                filename_match, text_match = \
                    self._check_attachments(attachments, v)

                if filename_match or text_match:
                    targets.add(k)

                if (filename_match and
                        'filename_attachments' not in
                        self._pb.score_properties):
                    self._pb.set_property_score("filename_attachments")

                if (text_match and
                        'text_attachments' not in self._pb.score_properties):
                    self._pb.set_property_score("text_attachments")

        # Check urls attachments
        # Target not added because urls come from attachments content
        if urls_attachments:
            for k, v in self._t_keys.iteritems():
                if 'urls_attachments' not in self._pb.score_properties:
                    if self._check_urls(urls_attachments, v):
                        self._pb.set_property_score("urls_attachments")

        # Check subject
        if swt(subject, self._s_keys):
            if 'mail_subject' not in self._pb.score_properties:
                self._pb.set_property_score("mail_subject")

        return self._pb.score, targets

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
