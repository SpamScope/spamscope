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
from collections import Counter
from modules import AbstractBolt, reformat_output
from modules.redis_client import Redis

try:
    import simplejson as json
except ImportError:
    import json


class OutputRedis(AbstractBolt):
    """Output tokenized mails on Redis servers. """

    def initialize(self, stormconf, context):
        super(OutputRedis, self).initialize(stormconf, context)

        # Load settings
        self._load_settings()

        # Init
        self._mails = []
        self._attachments = []
        self._counter = Counter(['mails', 'attachments'])

    def _load_settings(self):
        # Redis parameters
        servers = self.conf["servers"]
        self._flush_size = servers["flush_size"]
        self._queue_mails = servers["queue_mails"]
        self._queue_attachments = servers["queue_attachments"]

        # Redis class
        self._redis_client = Redis(
            hosts=servers["hosts"],
            shuffle_hosts=servers["shuffle_hosts"],
            port=servers["port"],
            db=servers["db"],
            password=servers["password"],
            reconnect_interval=servers["reconnect_interval"],
            max_retry=servers["max_retry"])

    def flush_mails(self):
        self._redis_client.push_messages(
            queue=self._queue_mails, messages=self._mails)
        self._mails = []
        self._counter["mails"] = 0

    def flush_attachments(self):
        self._redis_client.push_messages(
            queue=self._queue_attachments, messages=self._attachments)
        self._attachments = []
        self._counter["attachments"] = 0

    def process(self, tup):
        raw_mail = tup.values[1]

        # Convert back to object strings converted manually
        if raw_mail.get("network"):

            if raw_mail["network"].get("shodan"):
                raw_mail["network"]["shodan"] = json.loads(
                    raw_mail["network"]["shodan"])

            if raw_mail["network"].get("virustotal"):
                raw_mail["network"]["virustotal"] = json.loads(
                    raw_mail["network"]["virustotal"])

        # Reformat output
        mail, attachments = reformat_output(
            raw_mail, self.component_name)

        # Mails
        if mail:
            self._mails.append(json.dumps(mail, ensure_ascii=False))

            if self._counter["mails"] == self._flush_size:
                self.flush_mails()
            else:
                self._counter["mails"] += 1

        # Attachments
        for i in attachments:
            self._attachments.append(json.dumps(i, ensure_ascii=False))

            if self._counter["attachments"] == self._flush_size:
                self.flush_attachments()
            else:
                self._counter["attachments"] += 1

    def process_tick(self, freq):
        """Every freq seconds flush messages. """
        super(OutputRedis, self).process_tick(freq)

        if self._mails:
            self.log("Flush mails in Redis server after tick")
            self.flush_mails()

        if self._attachments:
            self.log("Flush attachments in Redis server after tick")
            self.flush_attachments()

        # Reload settings
        self._load_settings()
