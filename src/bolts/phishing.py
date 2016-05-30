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

from modules.utils import search_words
import re

try:
    import simplejson as json
except ImportError:
    import json


class Phishing(AbstractBolt):
    # TODO: Handling Tick Tuples reload keywords

    def initialize(self, stormconf, context):
        super(Phishing, self).initialize(stormconf, context)

        self.keywords = [
            "banca marche",
            "cartasi",
            "amazon",
            "dropbox",
            "aosta",
        ]

    def process(self, tup):
        sha256_random = tup.values[0]
        phishing = False

        try:
            mail = json.loads(tup.values[1])
            words_list = set(re.findall(r"[\w]+", mail.get("body")))

            if search_words(self.keywords, words_list):
                phishing = True
                self.log("Phishing for mail '{}'".format(sha256_random))

        except Exception as e:
            self.log(
                "Failed processing phishing for mail '{}".format(
                    sha256_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_random, phishing])
