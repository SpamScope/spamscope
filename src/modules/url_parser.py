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
from pyparsing import \
    Combine, \
    Group, \
    OneOrMore, \
    Optional, \
    Suppress, \
    Word, \
    alphanums, \
    delimitedList, \
    nums, \
    oneOf

import urlnorm
import logging

log = logging.getLogger(__name__)


def url_parser(url):

    '''
    Reference:
    https://www.accelebrate.com/blog/pyparseltongue-parsing-text-with-pyparsing://www.accelebrate.com/blog/pyparseltongue-parsing-text-with-pyparsing/

    URL grammar
    url ::= scheme '://' [userinfo] host [port] [path] [query] [fragment]
    scheme ::= http | https | ftp | file
    userinfo ::= url_chars+ ':' url_chars+ '@'
    host ::= alphanums | host (. + alphanums)
    port ::= ':' nums
    path ::= url_chars+
    query ::= '?' + query_pairs
    query_pairs ::= query_pairs | (query_pairs '&' query_pair)
    query_pair = url_chars+ '=' url_chars+
    fragment = '#' + url_chars
    url_chars = alphanums + '-_.~%+'
    '''

    url_chars = alphanums + '-_.~%+'

    fragment = Combine((Suppress('#') + Word(url_chars)))('fragment')

    scheme = oneOf('http https ftp file')('scheme')
    host = Combine(delimitedList(Word(url_chars), '.'))('host')
    port = Suppress(':') + Word(nums)('port')
    user_info = (
        Word(url_chars)('username') +
        Suppress(':') +
        Word(url_chars)('password') +
        Suppress('@')
    )

    query_pair = Group(Word(url_chars) + Suppress('=') + Word(url_chars))
    query = Group(Suppress('?') + delimitedList(query_pair, '&'))('query')

    path = Combine(
        Suppress('/') + OneOrMore(~query + Word(url_chars + '/'))
    )('path')

    url_parser = (
        scheme +
        Suppress('://') +
        Optional(user_info) +
        host +
        Optional(port) +
        Optional(path) +
        Optional(query) +
        Optional(fragment)
    )

    return url_parser.parseString(url)


def extract_urls(text, regex):
    results = dict()

    for i in regex.finditer(text):
        try:
            url = urlnorm.norm(i.group(1).strip())
            url_parsed = url_parser(url)
            if results.get(url_parsed.host):
                results[url_parsed.host].add(url)
            else:
                results[url_parsed.host] = set(url)
            log.debug("Parsed domain: {}".format(url_parsed.host))
        except urlnorm.InvalidUrl:
            log.warning("Parsing invalid url: {}".format(url))
        except:
            log.exception("Failed parsing url: {}".format(url))

    return results
