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
from collections import deque
from mailparser import MailParser
from modules.utils import fingerprints
from streamparse import Stream
from bolts.abstracts import AbstractBolt
import datetime
import os
import random

STRING = "string"
PATH = "path"


class InvalidMailFormat(ValueError):
    pass


class Tokenizer(AbstractBolt):
    """Split the mail in token parts (body, attachments, etc.). """

    outputs = [
        Stream(fields=['sha256_random', 'mail', 'is_filtered'], name='mail'),
        Stream(fields=['sha256_random', 'body', 'is_filtered'], name='body'),
        Stream(fields=['sha256_random', 'with_attachments', 'attachments'],
               name='attachments')]

    def initialize(self, stormconf, context):
        super(Tokenizer, self).initialize(stormconf, context)

        self._parser = MailParser()
        self._filter_mails_enabled = self.conf["filter_mails"]
        self._filter_attachments_enabled = self.conf["filter_attachments"]
        self._mails_analyzed = deque(maxlen=self.conf["maxlen_mails"])
        self._attachments_analyzed = deque(
            maxlen=self.conf["maxlen_attachments"])

    @property
    def filter_mails_enabled(self):
        return self._filter_mails_enabled

    @property
    def filter_attachments_enabled(self):
        return self._filter_attachments_enabled

    @property
    def parser(self):
        return self._parser

    def _filter_attachments(self):
        """
        Filter the attachments that are in memory, already analyzed
        """
        attachments = self.parser.attachments_list
        new_attachments = []

        for i in attachments:
            if i.get("content_transfer_encoding") == "base64":
                f = fingerprints(i["payload"].decode('base64'))
            else:
                f = fingerprints(i["payload"])

            if self.filter_attachments_enabled and \
                    f[1] in self._attachments_analyzed:
                new_attachments.append({
                    "md5": f[0],
                    "sha1": f[1],
                    "sha256": f[2],
                    "sha512": f[3],
                    "ssdeep": f[4],
                    "is_filtered": True})
            else:
                i["is_filtered"] = False
                new_attachments.append(i)

            self._attachments_analyzed.append(f[1])

        return new_attachments

    def _make_mail(self, tup):
        raw_mail = tup.values[0]
        mail_format = tup.values[4]
        rand = '_' + ''.join(random.choice('0123456789') for i in range(10))

        # Check if kind_data is correct
        if mail_format != STRING and mail_format != PATH:
            raise InvalidMailFormat(
                "Invalid mail format '{}'. Choose '{}' or '{}'".format(
                    mail_format, STRING, PATH))

        # Parsing mail
        if mail_format == PATH:
            if os.path.exists(raw_mail):
                self.parser.parse_from_file(raw_mail)
        else:
            self.parser.parse_from_string(raw_mail)

        # Getting all parts
        mail = self.parser.parsed_mail_obj

        # Data mail sources
        mail['mail_server'] = tup.values[1]
        mail['mailbox'] = tup.values[2]
        mail['priority'] = tup.values[3]

        # Fingerprints of body mail
        (mail['md5'], mail['sha1'], mail['sha256'], mail['sha512'],
            mail['ssdeep']) = fingerprints(self.parser.body.encode('utf-8'))
        sha256_rand = mail['sha256'] + rand

        # Add path to result
        if mail_format == PATH:
            mail['path_mail'] = raw_mail

        # Dates
        if mail.get('date'):
            mail['date'] = mail.get('date').isoformat()
        else:
            mail['date'] = datetime.datetime.utcnow().isoformat()

        mail['analisys_date'] = datetime.datetime.utcnow().isoformat()

        # Remove attachments
        mail.pop("attachments", None)

        return sha256_rand, raw_mail, mail

    def process(self, tup):
        try:
            sha256_rand, raw_mail, mail = self._make_mail(tup)
            with_attachments = False
            attachments = []

            # If mail is already analyzed
            if self.filter_mails_enabled and \
                    mail["sha1"] in self._mails_analyzed:
                mail.pop("body", None)
                body = ""
                is_filtered = True
            else:
                body = self.parser.body
                is_filtered = False

            # Emit mail
            self.emit([sha256_rand, mail, is_filtered], stream="mail")

            # Emit body
            self.emit([sha256_rand, body, is_filtered], stream="body")

            # Update databese mail analyzed
            self._mails_analyzed.append(mail["sha1"])

            # Emit only attachments
            if self.parser.attachments_list:
                attachments = self._filter_attachments()
                with_attachments = True

            self.emit([sha256_rand, with_attachments, attachments],
                      stream="attachments")

        except Exception as e:
            self.log("Failed parsing mail path: {}".format(raw_mail), "error")
            self.raise_exception(e, tup)
