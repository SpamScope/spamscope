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
from streamparse.bolt import Bolt

from modules.mail_parser import MailParser
from modules.utils import fingerprints
import datetime
import os
import random
import string

try:
    import simplejson as json
except ImportError:
    import json


MAIL_STRING = "string"
MAIL_PATH = "path"


class InvalidKindData(ValueError):
    pass


class Tokenizer(Bolt):
    """Split the mail in token parts (body, attachments, etc.). """

    def initialize(self, stormconf, context):
        self.p = MailParser()

    def random_message_id(self):
        random_s = ''.join(random.choice(string.lowercase) for i in range(20))
        return "<" + random_s + "@nothing-message-id>"

    def tokenizer(self, mail_server, mailbox, priority, mail_data, kind_data):

        # Mail object
        mail = self.p.parsed_mail_obj

        # Fingerprints of body mail
        (
            mail['md5'],
            mail['sha1'],
            mail['sha256'],
            mail['sha512'],
            mail['ssdeep'],
        ) = fingerprints(self.p.body.encode('utf-8'))

        # Data mail sources
        mail['mail_server'] = mail_server
        mail['mailbox'] = mailbox
        mail['priority'] = priority

        # Serialize mail
        mail_date = mail.get('date')

        if mail_date:
            mail['date'] = mail_date.isoformat()
        else:
            mail['date'] = datetime.datetime.utcnow().isoformat()

        mail['analisys_date'] = datetime.datetime.utcnow().isoformat()

        # Check message-id
        if not mail.get('message_id'):
            # to identify mail
            mail['message_id'] = self.random_message_id()

        if kind_data == MAIL_PATH:
            mail['path_mail'] = mail_data

        # Mail JSON
        mail_json = json.dumps(
            mail,
            ensure_ascii=False,
        )

        # if two mails have the same sha256
        random_s = '_' + ''.join(
            random.choice('0123456789') for i in range(10)
        )

        return mail['sha256'] + random_s, mail_json

    def process(self, tup):
        try:
            mail_data = tup.values[0]
            mail_server = tup.values[1]
            mailbox = tup.values[2]
            priority = tup.values[3]
            kind_data = tup.values[4]

            # Check if kind_data is correct
            if kind_data != MAIL_STRING and kind_data != MAIL_PATH:
                raise InvalidKindData(
                    "Invalid kind of data '{}'. Choose '{}' or '{}'".format(
                        kind_data,
                        MAIL_STRING,
                        MAIL_PATH,
                    )
                )

            # Parsing mail
            if kind_data == MAIL_PATH:
                if os.path.exists(mail_data):
                    self.p.parse_from_file(mail_data)

            else:
                self.p.parse_from_string(mail_data)

            # Tokenizer and emit
            self.emit(
                self.tokenizer(
                    mail_server, mailbox, priority, mail_data, kind_data
                )
            )

        except Exception as e:
            self.log(
                "Failed parsing mail path: {}".format(mail_data),
                "error"
            )
            self.raise_exception(e, tup)
