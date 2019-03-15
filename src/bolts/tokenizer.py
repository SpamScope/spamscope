#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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
from collections import deque
from cPickle import PickleError

from streamparse import Stream
import mailparser
from mailparser import get_header
from modules import (
    AbstractBolt,
    MAIL_PATH,
    MAIL_PATH_OUTLOOK,
    MAIL_STRING,
    dump_obj,
    load_obj)
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

    def __getattr__(self, name):
        return self.conf[name]

    def get_persistent_path(self, filter_name):
        return os.path.join(
            self.persistent_path, "{}.dump".format(filter_name))

    def initialize(self, stormconf, context):
        super(Tokenizer, self).initialize(stormconf, context)

        self.filter_types = ("mails", "attachments", "network")
        self.load_filters()

        self.mailparser = {
            MAIL_PATH: mailparser.parse_from_file,
            MAIL_PATH_OUTLOOK: mailparser.parse_from_file_msg,
            MAIL_STRING: mailparser.parse_from_string}

    def load_filters(self):
        for i in self.filter_types:
            if getattr(self, "filter_" + i):
                path = self.get_persistent_path(i)
                try:
                    obj = load_obj(path)
                    setattr(self, "analyzed_" + i, obj)
                except (IOError, EOFError, ValueError, PickleError):
                    setattr(self, "analyzed_" + i, deque(
                        maxlen=getattr(self, "maxlen_" + i)))

    def dump_filters(self):
        for i in self.filter_types:
            if getattr(self, "filter_" + i):
                path = self.get_persistent_path(i)
                dump_obj(path, getattr(self, "analyzed_" + i))
                self.log("Dumped RAM filter {!r} in {!r}".format(i, path))

    def _make_mail(self, tup):
        raw_mail = tup.values[0]
        mail_type = tup.values[5]
        rand = '_' + ''.join(random.choice('0123456789') for i in range(10))
        self.parser = self.mailparser[mail_type](raw_mail)

        # get only the mains headers because this number can explode
        # Elastic can't manage all possible headers
        mail = self.parser.mail_partial
        mail["headers"] = self.parser.headers_json

        # Data mail sources
        mail["mail_server"] = tup.values[1]
        mail["mailbox"] = tup.values[2]
        mail["priority"] = tup.values[3]
        mail["sender_ip"] = self.parser.get_server_ipaddress(tup.values[4])

        # Fingerprints of body mail
        (mail["md5"], mail["sha1"], mail["sha256"], mail["sha512"],
            mail["ssdeep"]) = fingerprints(self.parser.body.encode('utf-8'))
        sha256_rand = mail["sha256"] + rand

        if mail_type in (MAIL_PATH, MAIL_PATH_OUTLOOK):
            mail_string = raw_mail.split("/")[-1].replace(".processing", "")
            self.log("{}: {}".format(mail_string, mail["sha256"]))
            with open(raw_mail) as f:
                mail["size"] = len(f.read())
        elif mail_type in (MAIL_STRING):
            mail["size"] = len(raw_mail)

        # Add path to result
        if mail_type == MAIL_PATH:
            mail["mail_file"] = raw_mail.split("/")[-1].replace(
                ".processing", "")

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
        self.dump_filters()

    def process(self, tup):
        try:
            sha256_rand, mail = self._make_mail(tup)
            sha256 = sha256_rand.split("_")[0]
            self.log("Processing started: {}".format(sha256))
            with_attachments = False
            attachments = []
            body = self.parser.body
            raw_mail = tup.values[0]
            mail_type = tup.values[5]

            # If filter network is enabled
            is_filtered_net = False
            if self.filter_network:
                if mail["sender_ip"] in self.analyzed_network:
                    is_filtered_net = True

                # Update database ip addresses analyzed
                self.analyzed_network.append(mail["sender_ip"])

            # If filter mails is enabled
            is_filtered_mail = False
            if self.filter_mails:
                if mail["sha1"] in self.analyzed_mails:
                    mail.pop("body", None)
                    body = six.text_type()
                    raw_mail = six.text_type()
                    is_filtered_mail = True

                # Update database mails analyzed
                self.analyzed_mails.append(mail["sha1"])

            if self.parser.attachments:
                with_attachments = True
                attachments = MailAttachments.withhashes(
                    self.parser.attachments)

                # If filter attachments is enabled
                if self.filter_attachments:
                    hashes = attachments.filter(self.analyzed_attachments)
                    self.analyzed_attachments.extend(hashes)

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
