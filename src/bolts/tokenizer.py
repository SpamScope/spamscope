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
import random

try:
    import simplejson as json
except ImportError:
    import json


class Tokenizer(Bolt):

    def process(self, tup):
        try:
            mail_path = tup.values[0]
            mail_server = tup.values[1]
            mailbox = tup.values[2]
            priority = tup.values[3]

            # Parsing mail
            p = MailParser()
            p.parse_from_file(mail_path)
            mail = p.parsed_mail_obj

            # Fingerprints of body mail
            md5, sha1, sha256, sha512, ssdeep_ = fingerprints(
                p.body.encode('utf-8')
            )
            mail['md5'] = md5
            mail['sha1'] = sha1
            mail['sha256'] = sha256
            mail['sha512'] = sha512
            mail['ssdeep_'] = ssdeep_

            # Data mail sources
            mail['mail_server'] = mail_server
            mail['mailbox'] = mailbox
            mail['priority'] = priority

            # Serialize mail
            mail_date = mail.get('date')
            if mail_date:
                mail['date'] = mail_date.isoformat()

            mail_json = json.dumps(
                mail,
                ensure_ascii=False,
            )

            # if two mails have the same sha256
            random_s = '_' + ''.join(
                random.choice('0123456789') for i in range(10)
            )

            self.emit([sha256 + random_s, mail_json])

        except Exception as e:
            self.log(
                "Failed parsing mail path: {}".format(mail_path),
                "error"
            )
            self.raise_exception(e, tup)
