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


class Attachments(AbstractBolt):

    def initialize(self, stormconf, context):
        super(Attachments, self).initialize(stormconf, context)

    def process(self, tup):
        sha256_mail_random = tup.values[0]
        with_attachments = False
        attachments_json = None

        try:
            mail = json.loads(tup.values[1])
            attachments = mail.get('attachments', [])

            if attachments:
                from modules.sample_parser import SampleParser
                new_attachments = list()
                with_attachments = True

                self.log(
                    "Attachments for mail '{}'".format(sha256_mail_random)
                )

                for a in attachments:
                    new_attachments.append(
                        SampleParser().parse_sample_from_base64(
                            data=a['payload'],
                            filename=a['filename'],
                        )
                    )

                attachments_json = json.dumps(
                    new_attachments,
                    ensure_ascii=False,
                )

        except Exception as e:
            self.log(
                "Failed process attachments for mail: {}".format(
                    sha256_mail_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_mail_random, with_attachments, attachments_json])
