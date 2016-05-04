#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from pyparsing import CaselessLiteral
import hashlib
import ssdeep


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


def search_words(to_search, words_list):
    """
    Search list of words in the text.
    Examples:
        to_search = ["home water"]
        return True if in the text there are both words.
    """

    for key in to_search:
        count = 0
        words = key.split()

        for word in words:
            if CaselessLiteral(word).searchString(words_list):
                count += 1
        if count == len(words):
            return True

    return False
