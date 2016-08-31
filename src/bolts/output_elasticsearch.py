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
from elasticsearch import Elasticsearch
from elasticsearch import helpers
import datetime

try:
    import simplejson as json
except ImportError:
    import json


class OutputElasticsearch(AbstractBolt):
    """Output tokenized mails on Elasticsearch. """

    def initialize(self, stormconf, context):
        super(OutputElasticsearch, self).initialize(stormconf, context)

        # Elasticsearch parameters
        servers = self.conf['servers']
        self._index_prefix = servers['index.prefix']
        self._doc_type = servers['doc.type']
        self._flush_size = servers['flush_size']

        # Elasticsearch object
        self._es = Elasticsearch(
            hosts=servers['hosts'],
            sniff_on_start=True,
            sniff_on_connection_fail=True,
            sniffer_timeout=int(servers['sniffer.timeout']),
        )

        # Init
        self._mails = []
        self._count = 1

    def flush(self):
        helpers.bulk(self._es, self._mails)
        self._mails = []
        self._count = 1

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            mail = json.loads(tup.values[1])

            # Date for daily index
            timestamp = datetime.datetime.strptime(
                mail['analisys_date'],
                "%Y-%m-%dT%H:%M:%S.%f",
            )
            mail_date = timestamp.strftime("%Y.%m.%d")

            # Prepair mail for bulk
            mail['@timestamp'] = timestamp
            mail['_index'] = self._index_prefix + mail_date
            mail['_type'] = self._doc_type

            # Append mail in own date
            self._mails.append(mail)

            # Flush
            if self._count == self._flush_size:
                self.flush()
            else:
                self._count += 1

        except Exception as e:
            self.log(
                "Failed process json for mail: {}".format(sha256_random),
                "error"
            )
            self.raise_exception(e, tup)

    def process_tick(self, freq):
        """Every freq seconds flush messages. """
        super(OutputElasticsearch, self)._conf_loader()

        if self._mails:
            self.log("Flush mail in Redis server after tick")
            self.flush()
