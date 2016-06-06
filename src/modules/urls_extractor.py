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
import logging
import re
import urlnorm

try:
    from pyfaup.faup import Faup
except ImportError:
    raise ImportError(
        "Failed import Faup. Install it from: https://github.com/stricaud/faup"
    )

log = logging.getLogger(__name__)


class NotUnicodeError(ValueError):
    pass


class UrlsExtractor(object):

    def __init__(self):
        self._url_regex = re.compile(
            r'((?:(?:ht|f)tp(?:s?)\:\/\/)'
            r'(?:[!#$&-;=?-\[\]_a-z~]|%[0-9a-f]{2})+)',
            re.I
        )
        self._faup = Faup()

    def extract(self, text):
        """This function extract all url http(s) and ftp(s) from text.
        Return a dict, with a key for every second-level domain and
        value a list of disassembled urls (output Faup tool).

        Example disassembled url https://drive.google.com/drive/my-drive:

            {
                'domain': 'google.com',
                'domain_without_tld': 'google',
                'fragment': None,
                'host': 'drive.google.com',
                'port': None,
                'query_string': None,
                'resource_path': '/drive/my-drive',
                'scheme': 'https',
                'subdomain': 'drive',
                'tld': 'com',
                'url': 'https://drive.google.com/drive/my-drive'
            }

        """

        if not isinstance(text, unicode):
            raise NotUnicodeError("The given text is not in unicode")

        results = dict()

        for i in self._url_regex.finditer(text):

            try:
                url = urlnorm.norm(i.group(0).strip())
                self._faup.decode(url)
                tokens = self._faup.get()

                # Get results for domain
                domain = results.get(tokens['domain'], None)

                if domain:
                    domain.append(tokens)
                else:
                    results[tokens['domain']] = [tokens]

            except urlnorm.InvalidUrl:
                pass

        return results
