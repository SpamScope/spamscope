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
from collections import deque
from modules.sample_parser import SampleParser

try:
    import simplejson as json
except ImportError:
    import json


class Filter(AbstractBolt):
    """Filter attachments already analyzed. """

    outputs = ['sha256_random', 'attachments', 'with_attachments']

    def initialize(self, stormconf, context):
        super(Filter, self).initialize(stormconf, context)
        self._analyzed_attachments = deque(maxlen=self.conf["max_attachments"])

    def process(self, tup):
        sha256_random = tup.values[0]
        new_attachments = []
        attachments_json = None
        with_attachments = True

        try:
            attachments = json.loads(tup.values[1]).get('attachments', [])
            if attachments:
                with_attachments = True

            for i in attachments:
                sha1 = SampleParser.fingerprints_from_base64(i['payload'])[1]

                if sha1 not in self._analyzed_attachments:
                    new_attachments.append(i)

                self._analyzed_attachments.append(sha1)

            try:
                if new_attachments:
                    attachments_json = \
                        json.dumps(new_attachments, ensure_ascii=False)

            except UnicodeDecodeError:
                self.log("UnicodeDecodeError for mail '{}'".format(
                    sha256_random), "error")

        except Exception as e:
            self.log(
                "Failed filter mail: {}".format(sha256_random), "error")
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_random, attachments_json, with_attachments])
