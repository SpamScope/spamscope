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
from pyparsing import CaselessLiteral
import timeit
import re


keywords = [
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "nomatch",
    "laboramus eos"
]

keywords_re_compiled = []
for k in keywords:
    t = []
    w = k.split()
    for i in w:
        t.append(re.compile(r'(\b%s\b)' % i, re.I))
    keywords_re_compiled.append(t)

with open("samples/lorem_ipsum.txt") as f:
    text = f.read()


def search_words_pyparsing_set(text, keywords):
    words_list = set(re.findall(r"[\w]+", text))

    for key in keywords:
        count = 0
        words = key.split()

        for word in words:
            if CaselessLiteral(word).searchString(words_list):
                count += 1
        if count == len(words):
            return True

    return False


def search_words_pyparsing_list(text, keywords):
    words_list = re.findall(r"[\w]+", text)

    for key in keywords:
        count = 0
        words = key.split()

        for word in words:
            if CaselessLiteral(word).searchString(words_list):
                count += 1
        if count == len(words):
            return True

    return False


def search_words_regex(text, keywords):
    for key in keywords:
        count = 0
        words = key.split()

        for word in words:
            r = re.compile(r'(\b%s\b)' % word, re.I)
            if r.search(text):
                count += 1

        if count == len(words):
            return True

    return False


def search_words_regex_compiled(text, keywords):
    for key in keywords:
        count = 0

        for r in key:
            if r.search(text):
                count += 1

        if count == len(key):
            return True

    return False


def search_words_in_text(text, keywords):
    text = text.lower()

    for k in keywords:
        count = 0
        words = k.lower().split()

        for w in words:
            if w in text:
                count += 1

        if count == len(words):
            return True

    return False


if __name__ == "__main__":
    """Test results:

        search_words_pyparsing_set()    1.550626 sec
        search_words_pyparsing_list()   9.066026 sec
        search_words_regex()            0.044425 sec
        search_words_in_text()          0.007933 sec
        search_words_regex_compiled()   0.044599 sec
    """

    repeats = 15
    functions = [
        "search_words_pyparsing_set",
        "search_words_pyparsing_list",
        "search_words_regex",
        "search_words_in_text",
    ]

    for function in functions:
        t = timeit.Timer(
            "{0}(text, keywords)".format(function),
            "from __main__ import {0}, text, keywords".format(function),
        )
        sec = t.timeit(repeats) / repeats

        print("{function}()\t\t{sec:.6f} sec".format(**locals()))

    repeats = 15
    functions = [
        "search_words_regex_compiled",
    ]

    for function in functions:
        t = timeit.Timer(
            "{0}(text, keywords_re_compiled)".format(function),
            "from __main__ import {0}, text, keywords_re_compiled".format(
                function
            ),
        )
        sec = t.timeit(repeats) / repeats

        print("{function}()\t\t{sec:.6f} sec".format(**locals()))
