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
from modules.errors import ImproperlyConfigured
from modules.sample_parser import SampleParser
from modules.utils import load_config

try:
    import simplejson as json
except ImportError:
    import json


class Attachments(AbstractBolt):
    outputs = ['sha256_random', 'with_attachments', 'attachments']

    def initialize(self, stormconf, context):
        super(Attachments, self).initialize(stormconf, context)
        self._load_settings()

    def _load_settings(self):
        # Loading configuration
        self._load_lists()

        # Attachments handler
        self._sample_parser = SampleParser(
            blacklist_content_types=self._cont_type_bl)

    def _load_lists(self):

        # Load content types for blacklist
        self.log("Reloading content types list blacklist")
        self._cont_type_bl = set()
        for k, v in self.conf["content_types_blacklist"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, list):
                raise ImproperlyConfigured(
                    "Keywords content types blacklist \
                    list '{}' not valid".format(k)
                )
            keywords = [i.lower() for i in keywords]
            self._cont_type_bl |= set(keywords)
            self.log("Content types blacklist '{}' loaded".format(k))

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """
        super(Attachments, self)._conf_loader()
        self._load_settings()

    def process(self, tup):
        sha256_random = tup.values[0]
        with_attachments = tup.values[2]
        new_attachments = []
        attachments_json = None

        try:
            attachments = json.loads(tup.values[1]).get('attachments', [])

            for i in attachments:
                self._sample_parser.parse_sample_from_base64(
                    data=i['payload'],
                    filename=i['filename'],
                    mail_content_type=i['mail_content_type'],
                    transfer_encoding=i['content_transfer_encoding'],
                )

                if self._sample_parser.result:
                    new_attachments.append(self._sample_parser.result)

            try:
                if new_attachments:
                    attachments_json = json.dumps(
                        new_attachments,
                        ensure_ascii=False,
                    )
                    with_attachments = True

            except UnicodeDecodeError:
                self.log("UnicodeDecodeError for mail '{}'".format(
                    sha256_random), "error")

        except Exception as e:
            self.log("Failed process attachments for mail: {}".format(
                sha256_random), "error")
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_random, with_attachments, attachments_json])
