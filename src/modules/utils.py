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

from __future__ import unicode_literals
import hashlib
import logging
import os
import ssdeep
import yaml
from .exceptions import ImproperlyConfigured

log = logging.getLogger(__name__)


class MailItem(object):
    def __init__(
        self,
        filename,
        mail_server='localhost',
        mailbox='localhost',
        priority=None,
        trust=None,
    ):
        self.filename = filename
        self.mail_server = mail_server
        self.mailbox = mailbox
        self.priority = priority
        self.trust = trust
        self.timestamp = os.path.getctime(filename)

    def __cmp__(self, other):
        if self.priority > other.priority:
            return 1
        if self.priority < other.priority:
            return -1

        if self.timestamp > other.timestamp:
            return 1
        if self.timestamp < other.timestamp:
            return -1

        return 0


def fingerprints(data):
    # md5
    md5 = hashlib.md5()
    md5.update(data)
    md5 = md5.hexdigest()

    # sha1
    sha1 = hashlib.sha1()
    sha1.update(data)
    sha1 = sha1.hexdigest()

    # sha256
    sha256 = hashlib.sha256()
    sha256.update(data)
    sha256 = sha256.hexdigest()

    # sha512
    sha512 = hashlib.sha512()
    sha512.update(data)
    sha512 = sha512.hexdigest()

    # ssdeep
    ssdeep_ = ssdeep.hash(data)

    return md5, sha1, sha256, sha512, ssdeep_


def search_words_in_text(text, keywords):
    """Given a list of words return True if one or more
    lines are in text, else False.
    keywords format:
        keywords = [
            "word1 word2",
            "word3",
            "word4",
        ]
    (word1 AND word2) OR word3 OR word4
    """

    text = text.lower()

    for line in keywords:
        count = 0
        words = line.lower().split()

        for w in words:
            if w in text:
                count += 1

        if count == len(words):
            return True

    return False


def load_config(config_file):
    try:
        with open(config_file, 'r') as c:
            return yaml.load(c)
    except:
        log.exception("Config file {} not loaded".format(config_file))
        raise ImproperlyConfigured(
            "Config file {} not loaded".format(config_file))
