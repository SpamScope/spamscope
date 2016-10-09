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
            blacklist_content_types=self._cont_type_bl,
            virustotal_enabled=self.conf["virustotal"]["enabled"],
            tika_enabled=self.conf["tika"]["enabled"],
            virustotal_api_key=self.conf["virustotal"]["api_key"],
            tika_jar=self.conf["tika"]["path_jar"],
            tika_memory_allocation=self.conf["tika"]["memory_allocation"],
            tika_valid_content_types=self.tika_valid_content_types)

    def _load_lists(self):

        # Load content types for details
        self.tika_valid_content_types = set()
        if self.conf["tika"]["enabled"]:
            self.log("Reloading content types list for Tika details")
            for k, v in self.conf["tika"]["valid_content_types"].iteritems():
                keywords = load_config(v)
                if not isinstance(keywords, list):
                    raise ImproperlyConfigured(
                        "Keywords content types \
                        details list '{}' not valid".format(k))
                keywords = [i.lower() for i in keywords]
                self.tika_valid_content_types |= set(keywords)
                self.log("Content types Tika '{}' loaded".format(k))

        # Load content types for blacklist
        self.log("Reloading content types list blacklist")
        self._cont_type_bl = set()
        for k, v in self.conf["content_types_blacklist"].iteritems():
            keywords = load_config(v)
            if not isinstance(keywords, list):
                raise ImproperlyConfigured(
                    "Keywords content types blacklist \
                    list '{}' not valid".format(k))
            keywords = [i.lower() for i in keywords]
            self._cont_type_bl |= set(keywords)
            self.log("Content types blacklist '{}' loaded".format(k))

    def process_tick(self, freq):
        """Every freq seconds you reload the keywords. """
        super(Attachments, self)._conf_loader()
        self._load_settings()

    def process(self, tup):
        sha256_random = tup.values[0]
        with_attachments = tup.values[1]
        attachments = tup.values[2]
        new_attachments = []

        for i in attachments:
            try:
                self._sample_parser.parse_sample_from_base64(
                    data=i['payload'],
                    filename=i['filename'],
                    mail_content_type=i['mail_content_type'],
                    transfer_encoding=i['content_transfer_encoding'])

                result = self._sample_parser.result
                if result:
                    result['is_filtered'] = i.get('is_filtered')
                    new_attachments.append(result)

            except KeyError:
                new_attachments.append(i)

            except Exception as e:
                self.log("Failed process attachments for mail: {}".format(
                    sha256_random), "error")
                self.raise_exception(e, tup)

        self.emit([sha256_random, with_attachments, new_attachments])
