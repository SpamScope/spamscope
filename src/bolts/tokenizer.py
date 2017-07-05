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
import datetime
import os
import random
import six

import modules.spamassassin as spamassassin
from collections import deque
from mailparser import MailParser
from modules import AbstractBolt
from modules.attachments import fingerprints, MailAttachments
from streamparse import Stream

STRING = "string"
PATH = "path"


class InvalidMailFormat(ValueError):
    pass


class Tokenizer(AbstractBolt):
    """Split the mail in token parts (body, attachments, etc.). """

    outputs = [
        Stream(fields=['sha256_random', 'mail', 'is_filtered'], name='mail'),
        Stream(fields=['sha256_random', 'body', 'is_filtered'], name='body'),
        Stream(fields=['sha256_random', 'network', 'is_filtered'],
               name='network'),
        Stream(fields=['sha256_random', 'with_attachments', 'attachments'],
               name='attachments')]

    def initialize(self, stormconf, context):
        super(Tokenizer, self).initialize(stormconf, context)

        self._parser = MailParser()
        self._mails_analyzed = deque(maxlen=self.conf["maxlen_mails"])
        self._network_analyzed = deque(maxlen=self.conf["maxlen_network"])
        self._attachments_analyzed = deque(
            maxlen=self.conf["maxlen_attachments"])
        self._load_filters()

    def _load_filters(self):
        self._filter_mails_enabled = self.conf["filter_mails"]
        self._filter_network_enabled = self.conf["filter_network"]
        self._filter_attachments_enabled = self.conf["filter_attachments"]

    @property
    def filter_mails_enabled(self):
        return self._filter_mails_enabled

    @property
    def filter_network_enabled(self):
        return self._filter_network_enabled

    @property
    def filter_attachments_enabled(self):
        return self._filter_attachments_enabled

    @property
    def parser(self):
        return self._parser

    def _make_mail(self, tup):
        raw_mail = tup.values[0]
        mail_format = tup.values[5]
        rand = '_' + ''.join(random.choice('0123456789') for i in range(10))

        # Check if kind_data is correct
        if mail_format != STRING and mail_format != PATH:
            raise InvalidMailFormat(
                "Invalid mail format {!r}. Choose {!r} or {!r}".format(
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
        mail["mail_server"] = tup.values[1]
        mail["mailbox"] = tup.values[2]
        mail["priority"] = tup.values[3]
        mail["sender_ip"] = self.parser.get_server_ipaddress(tup.values[4])

        # Fingerprints of body mail
        (mail["md5"], mail["sha1"], mail["sha256"], mail["sha512"],
            mail["ssdeep"]) = fingerprints(self.parser.body.encode('utf-8'))
        sha256_rand = mail["sha256"] + rand

        # Add path to result
        if mail_format == PATH:
            mail["path_mail"] = raw_mail

        # Dates
        if mail.get('date'):
            mail["date"] = mail.get('date').isoformat()
        else:
            mail["date"] = datetime.datetime.utcnow().isoformat()

        mail["analisys_date"] = datetime.datetime.utcnow().isoformat()

        # Remove attachments
        mail.pop("attachments", None)

        return sha256_rand, mail

    def process_tick(self, freq):
        """Every freq seconds you reload configuration. """
        super(Tokenizer, self).process_tick(freq)
        self._load_filters()

    def process(self, tup):
        try:
            sha256_rand, mail = self._make_mail(tup)
            with_attachments = False
            attachments = []
            body = self.parser.body
            raw_mail = tup.values[0]
            mail_format = tup.values[5]

            # If filter network is enabled
            is_filtered_net = False
            if self.filter_network_enabled:
                if mail["sender_ip"] in self._network_analyzed:
                    is_filtered_net = True

                # Update databese mail analyzed
                self._network_analyzed.append(mail["sender_ip"])

            # If filter mails is enabled
            is_filtered_mail = False
            if self.filter_mails_enabled:
                if mail["sha1"] in self._mails_analyzed:
                    mail.pop("body", None)
                    body = six.text_type()
                    is_filtered_mail = True

                # Update databese mail analyzed
                self._mails_analyzed.append(mail["sha1"])

            # SpamAssassin integration
            # It's possible to use another bolt
            if not is_filtered_mail and self.conf["spamassassin"]["enabled"]:
                if mail_format == PATH:
                    mail["SpamAssassin"] = \
                        spamassassin.report_from_file(raw_mail)
                else:
                    mail["SpamAssassin"] = \
                        spamassassin.report_from_string(raw_mail)

            # Emit only attachments
            raw_attach = self.parser.attachments_list

            if raw_attach:
                with_attachments = True
                attachments = MailAttachments.withhashes(raw_attach)

                # If filter attachments is enabled
                if self.filter_attachments_enabled:
                    hashes = attachments.filter(self._attachments_analyzed)
                    self._attachments_analyzed.extend(hashes)

        except TypeError, e:
            self.raise_exception(e, tup)

        except UnicodeDecodeError, e:
            self.raise_exception(e, tup)

        else:
            # Emit network
            self.emit([sha256_rand, mail["sender_ip"], is_filtered_net],
                      stream="network")

            # Emit mail
            self.emit([sha256_rand, mail, is_filtered_mail], stream="mail")

            # Emit body
            self.emit([sha256_rand, body, is_filtered_mail], stream="body")

            self.emit([sha256_rand, with_attachments, list(attachments)],
                      stream="attachments")
