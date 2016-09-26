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
            tika_enabled=self.conf["tika"]["enabled"],
            tika_jar=self.conf["tika"]["path_jar"],
            tika_memory_allocation=self.conf["tika"]["memory_allocation"],
            tika_content_types=self._cont_type_details,
            blacklist_content_types=self._cont_type_bl,
            virustotal_enabled=self.conf["virustotal"]["enabled"],
            virustotal_api_key=self.conf["virustotal"]["api_key"],
        )

    def _load_lists(self):

        # Load content types for details
        self._cont_type_details = set()
        if self.conf["tika"]["enabled"]:
            self.log("Reloading content types list for Tika details")
            for k, v in self.conf["tika"]["content_types_details"].iteritems():
                keywords = load_config(v)
                if not isinstance(keywords, list):
                    raise ImproperlyConfigured(
                        "Keywords content types details \
                        list '{}' not valid".format(k)
                    )
                keywords = [i.lower() for i in keywords]
                self._cont_type_details |= set(keywords)
                self.log("Content types Tika '{}' loaded".format(k))

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
        sha256_mail_random = tup.values[0]
        with_attachments = False
        attachments_json = None

        try:
            mail = json.loads(tup.values[1])
            attachments = mail.get('attachments', [])

            if attachments:
                self.log(
                    "Attachments for mail '{}'".format(sha256_mail_random)
                )

                new_attachments = list()

                for a in attachments:
                    self._sample_parser.parse_sample_from_base64(
                        data=a['payload'],
                        filename=a['filename'],
                        mail_content_type=a['mail_content_type'],
                        transfer_encoding=a['content_transfer_encoding'],
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
                    self.log(
                        "UnicodeDecodeError for mail '{}'".format(
                            sha256_mail_random
                        ),
                        level="error"
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
