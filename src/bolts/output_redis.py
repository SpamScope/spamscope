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
from modules.redis_client import Redis


class OutputRedis(AbstractBolt):
    """Output tokenized mails on Redis servers. """

    def initialize(self, stormconf, context):
        super(OutputRedis, self).initialize(stormconf, context)

        # Redis parameters
        servers = self.conf['servers']
        self._flush_size = servers['flush_size']
        self._queue_name = servers['queue_name']
        self._mails = []
        self._count = 1

        # Redis class
        self._redis_client = Redis(
            hosts=servers['hosts'],
            shuffle_hosts=servers['shuffle_hosts'],
            port=servers['port'],
            db=servers['db'],
            password=servers['password'],
            reconnect_interval=servers['reconnect_interval'],
            max_retry=servers['max_retry'],
        )

    def flush(self):
        self._redis_client.push_messages(
            queue=self._queue_name,
            messages=self._mails,
        )
        self._mails = []
        self._count = 1

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            self._mails.append(tup.values[1])

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

        if self._mails:
            self.flush()
