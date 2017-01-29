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
from modules import (AbstractBolt, load_keywords_list, load_keywords_dict,
                     search_words_in_text as swt)
from modules.attachments import MailAttachments
from modules.bitmap import PhishingBitMap


def check_urls(urls, keywords):
    for domain, details in urls.iteritems():
        for i in details:
            if swt(i['url'], keywords):
                return True
    return False


def check_attachments(self, attachments, keywords):
    attach = MailAttachments(attachments)
    payloads = attach.payloadstext()
    filenames = attach.filenames()
    return swt(filenames, keywords), swt(payloads, keywords)


class Phishing(AbstractBolt):
    outputs = ['sha256_random', 'with_phishing', 'score', 'targets']

    def initialize(self, stormconf, context):
        super(Phishing, self).initialize(stormconf, context)

        # Input bolts for Phishing bolt
        self.input_bolts = set(context['source->stream->grouping'].keys())

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

        # If mail is filtered don't check for phishing
        is_filtered = greedy_data['tokenizer'][2]

        if is_filtered:
            return False, False

        # Reset phishing bitmap
        self._pb.reset_score()

        # Outputs
        targets = set()

        # Get all data
        mail = greedy_data['tokenizer'][1]
        body = mail.get('body')
        subject = mail.get('subject')
        from_ = mail.get('from')
        urls = greedy_data['urls-handler-body'][2]
        urls_attachments = greedy_data['urls-handler-attachments'][2]

        # TODO: if an attachment is filtered the score is not complete
        # more different mails can have same attachment
        attachments = greedy_data['attachments'][2]

        # Check body
        flag = False
        if body:
            for k, v in self._t_keys.iteritems():
                if swt(body, v):
                    targets.add(k)
                    flag = True
            if flag:
                self._pb.set_property_score("mail_body")

        # Check urls body
        # Target not added because urls come from body
        if urls:
            if any(check_urls(urls, v) for v in self._t_keys.values()):
                self._pb.set_property_score("urls_body")

        # Check from
        flag = False
        if from_:
            for k, v in self._t_keys.iteritems():
                if swt(from_, v):
                    targets.add(k)
                    flag = True
            if flag:
                self._pb.set_property_score("mail_from")

        # Check attachments filename and text match
        flag_text = False
        flag_filename = False
        if attachments:
            for k, v in self._t_keys.iteritems():
                filename_match, text_match = check_attachments(attachments, v)

                if filename_match or text_match:
                    targets.add(k)

                if filename_match:
                    flag_filename = True

                if text_match:
                    flag_text = True

            if flag_filename:
                self._pb.set_property_score("filename_attachments")

            if flag_text:
                self._pb.set_property_score("text_attachments")

        # Check urls attachments
        # Target not added because urls come from attachments content
        if urls_attachments:
            if any(check_urls(urls_attachments,
                              v) for v in self._t_keys.values()):
                self._pb.set_property_score("urls_attachments")

        # Check subject
        if swt(subject, self._s_keys):
            self._pb.set_property_score("mail_subject")

        return self._pb.score, list(targets)

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

            score, targets = self._search_phishing(
                self._mails.pop(sha256_random))

            if score:
                with_phishing = True

            self.emit([sha256_random, with_phishing, score, targets])
