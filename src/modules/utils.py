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

import copy
import datetime
import errno
import logging
import os
import re
import signal
import tempfile
import functools

import six
import yaml

RE_URL = re.compile(r'((?:(?:ht|f)tp(?:s?)\:\/\/)'
                    r'(?:[!#$&-;=?-\[\]_a-z~]|%[0-9a-f]{2})+)', re.I)

log = logging.getLogger(__name__)


class MailItem(object):
    def __init__(
        self,
        filename,
        mail_server='localhost',
        mailbox='localhost',
        priority=None,
        trust=None,
        mail_type=None,
        headers=[]
    ):
        self.filename = filename
        self.mail_server = mail_server
        self.mailbox = mailbox
        self.priority = priority
        self.trust = trust
        self.timestamp = os.path.getctime(filename)
        self.mail_type = mail_type
        self.headers = headers

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


class TimeoutError(Exception):
    pass


def timeout(seconds=10, error_message=os.strerror(errno.ETIME)):
    """
    This decorator raise an TimeoutError exception if the function
    takes more than 'seconds' seconds to terminate

    From: https://stackoverflow.com/questions/2281850/
    """
    def decorator(func):
        def _handle_timeout(signum, frame):
            raise TimeoutError(error_message)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, _handle_timeout)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


def write_payload(payload, extension, content_transfer_encoding="base64"):
    """This method writes the attachment payload on file system in temporary file.

    Args:
        payload (string): binary payload string in base64 to write on disk
        extension (string): file extension. Example '.js'
        content_transfer_encoding (string): designed to specify an invertible
                mapping between the "native" representation of a type of data
                and a representation that can be readily exchanged using 7 bit
                mail transport protocols

    Returns:
        Local file path of payload
    """

    temp = tempfile.mkstemp()[1] + extension

    if content_transfer_encoding == "base64":
        payload = payload.decode("base64")
        with open(temp, "wb") as f:
            f.write(payload)
    else:
        with open(temp, "w") as f:
            f.write(payload.encode("utf-8"))

    return temp


def urls_extractor(text, faup):
    """This function extract all url http(s) and ftp(s) from text.

    Args:
        text (string): text string with urls to extract

    Returns:
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

    # faup = Faup()
    text = six.text_type(text)
    results = {}

    for i in set(match.group().strip() for match in RE_URL.finditer(text)):
        faup.decode(i)
        tokens = faup.get()
        if tokens["domain"]:
            results.setdefault(tokens["domain"], []).append(tokens)
    else:
        return results


def search_words_given_key(text, key_value):
    """Given a key - value tuple return the key if the value in text.

    Args:
        text (string): text to check
        key_value (tuple): key is a string and value a list

    Returns:
        key if value in text
    """
    key, value = key_value

    if search_words_in_text(text, value):
        return key


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
    keywords = {six.text_type(k).lower() for k in keywords}

    for line in keywords:
        if all(True if w in text else False for w in line.split()):
            return True

    return False


def load_config(config_file):
    try:
        with open(config_file, 'r') as c:
            return yaml.load(c)
    except:
        message = "Config file {} not loaded".format(config_file)
        log.exception(message)
        raise RuntimeError(message)


def load_keywords_list(obj_paths, lower=True):
    keywords = set()

    if not obj_paths:
        return keywords

    for k, v in obj_paths.iteritems():
        temp = load_config(v)

        if not isinstance(temp, list):
            raise RuntimeError("List {!r} not valid".format(k))

        if lower:
            keywords |= {six.text_type(i).lower() for i in temp}
        else:
            keywords |= {six.text_type(i) for i in temp}

    return keywords


def load_keywords_dict(obj_paths, lower=True):
    keywords = {}

    if not obj_paths:
        return keywords

    for k, v in obj_paths.iteritems():
        temp = load_config(v)

        if not isinstance(temp, dict):
            raise RuntimeError("List {!r} not valid".format(k))

        keywords.update(temp)

    if lower:
        keywords_lower = {}
        for k, v in keywords.iteritems():
            keywords_lower[k] = {six.text_type(i).lower() for i in v}
        return keywords_lower
    else:
        keywords_str = {}
        for k, v in keywords.iteritems():
            keywords_str[k] = {six.text_type(i) for i in v}
        return keywords_str


def reformat_output(mail=None, bolt=None, **kwargs):
    """ This function replaces the standard SpamScope JSON output.
    The output is splitted in two parts: mail and attachments.
    In mail part are reported only the hashes of attachments.
    In attachments part the archived files are reported in root with the
    archive files.

    Args:
        mail (dict): raw SpamScope output
        bolt (string): only bolt can reformat the output
        kwargs:
            elastic_index_mail: prefix of Elastic index for mails
            elastic_index_attach: prefix of Elastic index for attachments
            elastic_type_mail: prefix of Elastic doc_type for mails
            elastic_type_attach: prefix of Elastic doc_type for attachments

    Returns:
        (mail, attachments):
            mail (dict): Python object with mail details
            attachments(list): Python list with all attachments details
    """

    if bolt not in ('output-elasticsearch', 'output-redis'):
        message = "Bolt {!r} not in list of permitted bolts".format(bolt)
        log.exception(message)
        raise RuntimeError(message)

    if mail:
        mail = copy.deepcopy(mail)
        attachments = []

        if bolt == "output-elasticsearch":
            # Date for daily index
            try:
                timestamp = datetime.datetime.strptime(
                    mail["analisys_date"], "%Y-%m-%dT%H:%M:%S.%f")
            except:
                # Without microseconds
                timestamp = datetime.datetime.strptime(
                    mail["analisys_date"], "%Y-%m-%dT%H:%M:%S")

            mail_date = timestamp.strftime("%Y.%m.%d")

        # Get a copy of attachments
        raw_attachments = []
        if mail.get("attachments", []):
            raw_attachments = copy.deepcopy(mail["attachments"])

        # Prepair attachments for bulk
        for i in raw_attachments:
            i["is_archived"] = False

            if bolt == "output-elasticsearch":
                i["@timestamp"] = timestamp
                i["_index"] = kwargs["elastic_index_attach"] + mail_date
                i["_type"] = kwargs["elastic_type_attach"]
                i["type"] = kwargs["elastic_type_attach"]

            for j in i.get("files", []):
                f = copy.deepcopy(j)

                # Prepair archived files
                f["is_archived"] = True

                if bolt == "output-elasticsearch":
                    f["@timestamp"] = timestamp
                    f["_index"] = kwargs["elastic_index_attach"] + mail_date
                    f["_type"] = kwargs["elastic_type_attach"]
                    f["type"] = kwargs["elastic_type_attach"]

                attachments.append(f)

                # Remove from archived payload and attachments post processing
                # now in root
                j.pop("payload", None)
                j.pop("virustotal", None)
                j.pop("thug", None)
                j.pop("zemana", None)

            attachments.append(i)

        # Remove from mail the attachments huge fields like payload
        # Fetch from Elasticsearch more fast
        for i in mail.get("attachments", []):
            i.pop("payload", None)
            i.pop("tika", None)
            i.pop("virustotal", None)
            i.pop("thug", None)
            i.pop("zemana", None)

            for j in i.get("files", []):
                j.pop("payload", None)
                j.pop("virustotal", None)
                j.pop("thug", None)
                j.pop("zemana", None)

        # Prepair mail for bulk
        if bolt == "output-elasticsearch":
            mail["@timestamp"] = timestamp
            mail["_index"] = kwargs["elastic_index_mail"] + mail_date
            mail["type"] = kwargs["elastic_type_mail"]
            mail["_type"] = kwargs["elastic_type_mail"]

        return mail, attachments


def register(processors, active=True):
    """Add processor to set of processors.
    From the best Python book Fluent Python (https://github.com/fluentpython).
    Thanks a lot Luciano Ramalho.

    Args:
        processors (set): where store the active functions
        active (bool): if True adds the function, viceversa removes it

    Returns:
        decorator
    """

    def decorate(func):
        if active:
            processors.add(func)
        else:
            processors.discard(func)

        return func

    return decorate


def load_whitelist(whitelists):
    """
    Given a dict with this structure:

        alexa:
            path: /path/to/alexa
            expiry: 2016-06-28T12:33:00.000Z # date ISO 8601 only UTC
        test1:
            path: /path/to/test1
            expiry:
        test2:
            path: /path/to/test2

    return a set with all domains in whitelist.

    Args:
        whitelists (dict): dict of lists of domains

    Returns:
        set of all domains in all lists.
    """

    whitelist = set()

    if not whitelists:
        return whitelist

    for k, v in whitelists.iteritems():
        expiry = v.get('expiry')
        reload_ = True

        if expiry:
            now = datetime.datetime.utcnow()
            reload_ = bool(datetime.datetime.strptime(
                expiry, "%Y-%m-%dT%H:%M:%S.%fZ") > now)

        if reload_:
            domains = load_config(v["path"])

            if not isinstance(domains, list):
                raise RuntimeError(
                    "Whitelist {!r} not loaded".format(k))

            domains = {i.lower() for i in domains}
            whitelist |= domains

    return whitelist


def text2urls_whitelisted(text, whitelist, faup):
    """
    Given text and whitelist return all urls in text not in
    whitelist (domains whitelist).

    Args:
        text (string): text to analyze to extract urls
        whitelist (set): set with all domains in whitelist

    Returns:
        Return a dict, with a key for every second-level domain and
        value a list of disassembled urls (output Faup tool).
    """

    urls = {}

    if text:
        urls = urls_extractor(text, faup)
        domains = urls.keys()

        for d in domains:
            if d.lower() in whitelist:
                urls.pop(d)

    return urls


def reformat_urls(urls):
    """
    Change urls format to store them in Elasticsearch (dot . issue)

    Args:
        urls (dict): output of urls_extractor

    Returns:
        list of all urls
    """

    new_urls = []

    for v in urls.values():
        new_urls.extend(v)

    return new_urls
