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
import random
import six
from collections import deque

from streamparse import Stream
import mailparser
from mailparser import get_header
from modules import AbstractBolt, MAIL_PATH, MAIL_STRING, MAIL_PATH_OUTLOOK
from modules.attachments import fingerprints, MailAttachments


class Tokenizer(AbstractBolt):
    """Split the mail in token parts (body, attachments, etc.) and sends
    these parts to others bolts."""

    outputs = [
        Stream(
            fields=['sha256_random', 'mail', 'is_filtered'],
            name='mail'),
        Stream(
            fields=['sha256_random', 'raw_mail', 'mail_type', 'is_filtered'],
            name='raw_mail'),
        Stream(
            fields=['sha256_random', 'body', 'is_filtered'],
            name='body'),
        Stream(
            fields=['sha256_random', 'network', 'is_filtered'],
            name='network'),
        Stream(
            fields=['sha256_random', 'with_attachments', 'attachments'],
            name='attachments')]

    def initialize(self, stormconf, context):
        super(Tokenizer, self).initialize(stormconf, context)

        self.mailparser = {
            MAIL_PATH: mailparser.parse_from_file,
            MAIL_PATH_OUTLOOK: mailparser.parse_from_file_msg,
            MAIL_STRING: mailparser.parse_from_string}

        self.mails_analyzed = deque(maxlen=self.conf["maxlen_mails"])
        self.network_analyzed = deque(maxlen=self.conf["maxlen_network"])
        self.attachments_analyzed = deque(
            maxlen=self.conf["maxlen_attachments"])

        self._load_filters()

    def _load_filters(self):
        self.filter_mails_enabled = self.conf["filter_mails"]
        self.filter_network_enabled = self.conf["filter_network"]
        self.filter_attachments_enabled = self.conf["filter_attachments"]

    def _make_mail(self, tup):
        raw_mail = tup.values[0]
        mail_type = tup.values[5]
        rand = '_' + ''.join(random.choice('0123456789') for i in range(10))
        self.parser = self.mailparser[mail_type](raw_mail)
        mail = self.parser.mail

        # Data mail sources
        mail["mail_server"] = tup.values[1]
        mail["mailbox"] = tup.values[2]
        mail["priority"] = tup.values[3]
        mail["sender_ip"] = self.parser.get_server_ipaddress(tup.values[4])
        mail["to_domains"] = self.parser.to_domains

        # Fingerprints of body mail
        (mail["md5"], mail["sha1"], mail["sha256"], mail["sha512"],
            mail["ssdeep"]) = fingerprints(self.parser.body.encode('utf-8'))
        sha256_rand = mail["sha256"] + rand

        # Add path to result
        if mail_type == MAIL_PATH:
            mail["path_mail"] = raw_mail

        # Dates
        if mail.get('date'):
            mail["date"] = mail.get('date').isoformat()
        else:
            mail["date"] = datetime.datetime.utcnow().isoformat()

        mail["analisys_date"] = datetime.datetime.utcnow().isoformat()

        # Adding custom headers
        for h in tup.values[6]:
            mail["custom_" + h] = get_header(self.parser.message, h)

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
            mail_type = tup.values[5]

            # If filter network is enabled
            is_filtered_net = False
            if self.filter_network_enabled:
                if mail["sender_ip"] in self.network_analyzed:
                    is_filtered_net = True

                # Update database ip addresses analyzed
                self.network_analyzed.append(mail["sender_ip"])

            # If filter mails is enabled
            is_filtered_mail = False
            if self.filter_mails_enabled:
                if mail["sha1"] in self.mails_analyzed:
                    mail.pop("body", None)
                    body = six.text_type()
                    raw_mail = six.text_type()
                    is_filtered_mail = True

                # Update database mails analyzed
                self.mails_analyzed.append(mail["sha1"])

            if self.parser.attachments:
                with_attachments = True
                attachments = MailAttachments.withhashes(
                    self.parser.attachments)

                # If filter attachments is enabled
                if self.filter_attachments_enabled:
                    hashes = attachments.filter(self.attachments_analyzed)
                    self.attachments_analyzed.extend(hashes)

        except TypeError, e:
            self.raise_exception(e, tup)

        except UnicodeDecodeError, e:
            self.raise_exception(e, tup)

        else:
            # Emit mail
            self.emit([sha256_rand, mail, is_filtered_mail], stream="mail")

            # Emit raw_mail
            self.emit([
                sha256_rand, raw_mail, mail_type, is_filtered_mail],
                stream="raw_mail")

            # Emit body
            self.emit([sha256_rand, body, is_filtered_mail], stream="body")

            # Emit network
            self.emit([
                sha256_rand, mail["sender_ip"], is_filtered_net],
                stream="network")

            # Emit attachments
            self.emit([
                sha256_rand, with_attachments, list(attachments)],
                stream="attachments")
