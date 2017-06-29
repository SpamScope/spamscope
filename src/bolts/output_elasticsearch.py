#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from modules import AbstractBolt, reformat_output
from elasticsearch import Elasticsearch, helpers

try:
    import simplejson as json
except ImportError:
    import json


class OutputElasticsearch(AbstractBolt):
    """Output tokenized mails on Elasticsearch. """

    def initialize(self, stormconf, context):
        super(OutputElasticsearch, self).initialize(stormconf, context)

        # Load settings
        self._load_settings()

        # Init
        self._mails = []
        self._attachments = []
        self._count = 1

    def _load_settings(self):
        # Elasticsearch parameters
        servers = self.conf["servers"]
        self._flush_size = servers["flush_size"]

        # Parameters for reformat_output function
        self._parameters = {
            "elastic_index_mail": servers["index.prefix.mails"],
            "elastic_type_mail": servers["doc.type.mails"],
            "elastic_index_attach": servers["index.prefix.attachments"],
            "elastic_type_attach": servers["doc.type.attachments"]}

        # Elasticsearch object
        self._es = Elasticsearch(hosts=servers["hosts"])

    def flush(self):
        helpers.bulk(self._es, self._mails)
        helpers.bulk(self._es, self._attachments)
        self._mails = []
        self._attachments = []
        self._count = 1

    def process(self, tup):
        raw_mail = tup.values[1]

        # Convert back to object strings convert manually
        if raw_mail.get("network"):

            if raw_mail["network"].get("shodan"):
                raw_mail["network"]["shodan"] = json.loads(
                    raw_mail["network"]["shodan"])

            if raw_mail["network"].get("virustotal"):
                raw_mail["network"]["virustotal"] = json.loads(
                    raw_mail["network"]["virustotal"])

        # Reformat output
        mail, attachments = reformat_output(
            raw_mail, self.component_name, **self._parameters)

        self._mails.append(mail)
        self._attachments += attachments

        # Flush
        if self._count == self._flush_size:
            self.flush()
        else:
            self._count += 1

    def process_tick(self, freq):
        """Every freq seconds flush messages. """
        super(OutputElasticsearch, self).process_tick(freq)

        # Reload settings
        self._load_settings()

        # Flush mails
        if self._mails or self._attachments:
            self.log("Flush mails/attachments in Elasticsearch after tick")
            self.flush()
