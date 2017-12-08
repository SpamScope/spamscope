#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

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
from functools import partial
import json

from lxml import html
from lxml.etree import ParserError
import six

from ..utils import (search_words_in_text as swt,
                     search_words_given_key as swgk)
from ..attachments import MailAttachments
from ..bitmap import PhishingBitMap


def check_form(body):
    """
    Check the presence of forms action.

    Args:
        body (string): body to check

    Returns:
        boolean True if there is form
    """

    # http://lxml.de/parsing.html - Python unicode strings
    body = body.encode("utf-8")

    if body.strip():
        try:
            tree = html.fromstring(body)
        except ParserError:
            return False
        else:
            results = tree.xpath('//form')
            if results:
                return True

    return False


def check_urls(urls, keywords):
    """
    Check the keywords in urls.

    Args:
        urls (dict): output of urls_extractor function
        keywords (list): list of keywords

    Returns:
        boolean True if any keywords is in urls
    """

    for domain, details in urls.iteritems():
        for i in details:
            if swt(i["url"], keywords):
                return True
    return False


def check_phishing(**kwargs):
    """
    Check in every email parts the presence of any keywords.
    Return a targets list and a custom phishing score.

    Args:
        email (dict): email object from mailparser library
        attachments (list): list of email attachments from mailparser
        urls_body (list): list of urls from body
        urls_attachments (list): list of urls from attachments
        target_keys (dict): dict wit keys targets and values keywords
        subject_keys (list): list of subject keys

    Returns:
        dict with results
    """

    # Init parameters
    with_urls = False
    targets = set()
    bitmap = PhishingBitMap()
    email = kwargs["email"]
    attachments = kwargs["attachments"]
    urls_body = kwargs["urls_body"]
    urls_attachments = kwargs["urls_attachments"]
    target_keys = kwargs["target_keys"]
    subject_keys = kwargs["subject_keys"]

    # Get all data
    body = email.get('body', six.text_type())
    subject = email.get('subject', six.text_type())
    # from mailparser 3.0.0 from is an object
    from_ = email.get('from', six.text_type())
    from_ = json.dumps(from_, ensure_ascii=False)

    # TODO: if an attachment is filtered, the score is not complete
    # many different mails can have the same attachment
    # many different attachments can have the same mail
    attachments = MailAttachments(attachments)

    urls = (
        (urls_body, 'urls_body'),
        (urls_attachments, 'urls_attachments'))

    # Mapping for targets checks
    mapping_targets = (
        (body, 'mail_body'),
        (from_, 'mail_from'),
        (attachments.payloadstext(), 'text_attachments'),
        (attachments.filenamestext(), 'filename_attachments'))

    for k, v in mapping_targets:
        if k:
            matcher = partial(swgk, k)
            t = set(i for i in map(matcher, target_keys.iteritems()) if i)
            if t:
                targets |= t
                bitmap.set_property_score(v)

    # Check urls
    # Target not added because urls come already analyzed text
    for k, v in urls:
        if k:
            with_urls = True
            if any(check_urls(k, i) for i in target_keys.values()):
                bitmap.set_property_score(v)

    # Check subject
    if swt(subject, subject_keys):
        bitmap.set_property_score("mail_subject")

    # Check form
    if check_form(body):
        bitmap.set_property_score("mail_form")

    results = {"score": bitmap.score,
               "score_expanded": bitmap.score_properties,
               "targets": list(targets),
               "with_phishing": True if bitmap.score and with_urls else False}

    return results
