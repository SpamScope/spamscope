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
from modules.phishing_bitmap import PhishingBitMap


class JsonMaker(Bolt):
    outputs = ['sha256_random', 'json']

    def initialize(self, stormconf, context):
        self.mails = {}
        self.input_bolts = set(context['source->stream->grouping'].keys())

        # Phishing bitmap
        self._phishing_bitmap = PhishingBitMap()

    def _compose_output(self, greedy_data):
        # Tokenizer
        mail = greedy_data['tokenizer'][1]
        mail['is_filtered'] = greedy_data['tokenizer'][2]

        # Add intelligence output only if mail is not filtered
        if not mail['is_filtered']:

            # Phishing
            phishing_score = greedy_data['phishing'][2]
            mail['with_phishing'] = greedy_data['phishing'][1]
            mail['phishing_score'] = phishing_score

            if phishing_score:
                self._phishing_bitmap.score = phishing_score

                mail['targets'] = greedy_data['phishing'][3]
                mail['phishing_score_expanded'] = \
                    self._phishing_bitmap.score_properties

            # Forms
            mail['with_forms'] = greedy_data['forms'][1]

            # Urls in body
            mail['with_urls_body'] = greedy_data['urls-handler-body'][1]
            if mail['with_urls_body']:

                # Change urls format to fix Elasticsearch issue with dot '.'
                reformat_urls = []
                urls = greedy_data['urls-handler-body'][2]

                for v in urls.values():
                    reformat_urls.extend(v)

                mail['urls_body'] = reformat_urls

            # Urls in attachments
            mail['with_urls_attachments'] = \
                greedy_data['urls-handler-attachments'][1]
            if mail['with_urls_attachments']:

                # Change urls format to fix Elasticsearch issue with dot '.'
                reformat_urls = []
                urls = greedy_data['urls-handler-attachments'][2]

                for v in urls.values():
                    reformat_urls.extend(v)

                mail['urls_attachments'] = reformat_urls

        # Attachments
        mail['with_attachments'] = greedy_data['attachments'][1]
        if mail['with_attachments']:
            mail['attachments'] = greedy_data['attachments'][2]

        return mail

    def process(self, tup):
        try:
            bolt = tup.component
            sha256_random = tup.values[0]
            values = tup.values

            if self.mails.get(sha256_random, None):
                self.mails[sha256_random][bolt] = values
            else:
                self.mails[sha256_random] = {bolt: values}

            diff = self.input_bolts - set(self.mails[sha256_random].keys())
            if not diff:
                output_json = self._compose_output(
                    self.mails.pop(sha256_random))

                self.log("New JSON for mail '{}'".format(
                    sha256_random), "debug")

                self.emit([sha256_random, output_json])

        except Exception as e:
            self.log("Failed process json for mail: {}".format(
                sha256_random), "error")
            self.raise_exception(e, tup)
