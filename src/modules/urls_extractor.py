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

# from __future__ import unicode_literals
import logging
import re

try:
    import simplejson as json
except ImportError:
    import json

try:
    from pyfaup.faup import Faup
except ImportError:
    raise ImportError(
        "Failed import Faup. Install it from: https://github.com/stricaud/faup"
    )

log = logging.getLogger(__name__)


class NotUnicodeError(ValueError):
    pass


class FailedFaupParsing(Exception):
    pass


class FailedRegexUrl(Exception):
    pass


class FailedReturnJsonUrls(Exception):
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

        self._results = dict()

        for i in self._url_regex.finditer(text):

            try:
                """
                import urlnorm
                url = urlnorm.norm(i.group(0).strip())

                Can't use urlnorm because can't manage domain like
                http://contentsr,xn--90afavbplfx2a6a5b2a,xn--p1ai/

                After norm it's impossible tokenize this kind of urls
                """

                url = i.group(0).strip()
            except:
                raise FailedRegexUrl("Failed parsing regex urls")

            try:
                self._faup.decode(url)
                tokens = self._faup.get()

                # Get results for domain
                domain = self._results.get(tokens['domain'], None)

                if domain:
                    domain.append(tokens)
                else:
                    self._results[tokens['domain']] = [tokens]

            except:
                raise FailedFaupParsing("Failed tokenize url with Faup")

    @property
    def urls_obj(self):
        return self._results

    @property
    def urls_json(self):
        try:
            return json.dumps(
                self.urls_obj,
                ensure_ascii=False
            )
        except:
            raise FailedReturnJsonUrls("Failed make JSON from urls result")
