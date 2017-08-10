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

import logging
import redis
import time
from random import shuffle


log = logging.getLogger(__name__)


class RedisConnectionFailed(Exception):
    pass


class Redis:
    """This class will send events to a Redis queue using RPUSH.
    The RPUSH command is supported in Redis v0.0.7+.
    For more information, see http://redis.io/[the Redis homepage]

    hosts:
    The hostname(s) of your Redis server(s). Ports may be specified on any
    hostname, which will override the global port config.
    If the hosts list is an array, it will pick one random host to connect to,
    if that host is disconnected it will then pick another.

    For example:
        "127.0.0.1"
        ["127.0.0.1", "127.0.0.2"]
        ["127.0.0.1:6380", "127.0.0.1"]

    shuffle_hosts:
    Shuffle the host list during connection.

    port:
    The default port to connect on. Can be overridden on any host.

    db:
    The Redis database number.

    password:
    Password to authenticate with.  There is no authentication by default.

    reconnect_interval:
    Interval for reconnecting to failed Redis connections.

    max_retry:
    number of connect retries
    """

    def __init__(
        self,
        hosts=["127.0.0.1"],
        shuffle_hosts=True,
        port=6379,
        db=0,
        password=None,
        reconnect_interval=1,
        max_retry=60,
    ):
        # Parameters
        self._hosts = hosts
        self._shuffle_hosts = shuffle_hosts
        self._port = port
        self._db = db
        self._password = password
        self._reconnect_interval = reconnect_interval
        self._max_retry = max_retry
        self._current_retry = max_retry

        self._register()

    @property
    def hosts(self):
        return self._hosts

    @property
    def shuffle_hosts(self):
        return self._shuffle_hosts

    @property
    def port(self):
        return self._port

    @property
    def db(self):
        return self._db

    @property
    def password(self):
        return self._password

    @property
    def reconnect_interval(self):
        return self._reconnect_interval

    @property
    def max_retry(self):
        return self._max_retry

    @max_retry.setter
    def max_retry(self, value):
        self._max_retry = value

    def _get_host_port(self, server):
        server = server.split(":")
        host = None
        port = None

        try:
            host, port = server
        except:
            host = server[0]

        return host, port

    def _register(self):
        if not isinstance(self.hosts, list) and \
                not isinstance(self.hosts, str):
            log.exception("hosts must be 'list' or 'string'")
            raise RuntimeError("hosts must be 'list' or 'string'")

        if isinstance(self.hosts, list):
            if self.shuffle_hosts:
                shuffle(self.hosts)
            self._host_idx = 0

    def connect(self):
        if isinstance(self.hosts, str):
            hosts = self.hosts
        else:
            hosts = self.hosts[self._host_idx]
            n_host_idx = self._host_idx + 1
            self._host_idx = n_host_idx if n_host_idx < len(self.hosts) else 0

        self._currenthost, currentport = self._get_host_port(hosts)

        if currentport:
            self._port = currentport

        # Connect to Redis
        self._redis = redis.StrictRedis(
            host=self._currenthost,
            port=self.port,
            db=self.db,
            password=self.password)

    def push_messages(self, queue=None, messages=None):

        if not queue:
            log.exception("queue not defined")
            raise RuntimeError("Must define a queue")

        try:
            # Connect to Redis server
            self.connect()

            # Push messages
            self._redis.rpush(queue, *messages)

            # Reset current_retry
            self._current_retry = self.max_retry

        except:
            log.warning(
                "Failed to push messages in Redis server".format(self.hosts))

            if not self._current_retry:
                log.exception("Redis connection failed for {} times".format(
                    self.max_retry))
                raise RedisConnectionFailed(
                    "Redis connection failed for {} times".format(
                        self.max_retry))

            time.sleep(self._reconnect_interval)

            self._current_retry -= 1
            log.warning("Current retry is {}".format(self._current_retry))
            self.push_messages(queue, messages)
