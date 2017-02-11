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
import logging
import os
import re
import six
import tempfile
import yaml
from .exceptions import ImproperlyConfigured

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


def write_payload(payload, extension):
    """This method writes the attachment payload on file system in temporary file.

    Args:
        payload (string): binary payload string in base64 to write on disk
        extension (string): file extension. Example '.js'

    Returns:
        Local file path of payload
    """

    temp = tempfile.mkstemp()[1] + extension

    with open(temp, 'wb') as f:
        f.write(payload.decode('base64'))

    return temp


def urls_extractor(faup_parser, text):
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

    text = six.text_type(text)
    results = {}

    for i in set(match.group().strip() for match in RE_URL.finditer(text)):
        faup_parser.decode(i)
        tokens = faup_parser.get()
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
    keywords = {k.lower() for k in keywords}

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
        raise ImproperlyConfigured(message)


def load_keywords_list(obj_paths, lower=True):
    keywords = set()

    for k, v in obj_paths.iteritems():
        temp = load_config(v)

        if not isinstance(temp, list):
            raise ImproperlyConfigured("List {!r} not valid".format(k))

        if lower:
            keywords |= {i.lower() for i in temp}
        else:
            keywords |= set(temp)

    return keywords


def load_keywords_dict(obj_paths, lower=True):
    keywords = {}

    for k, v in obj_paths.iteritems():
        temp = load_config(v)

        if not isinstance(temp, dict):
            raise ImproperlyConfigured("List {!r} not valid".format(k))

        keywords.update(temp)

    if lower:
        keywords_lower = {}
        for k, v in keywords.iteritems():
            keywords_lower[k] = {i.lower() for i in v}
        return keywords_lower

    return keywords


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
        raise ImproperlyConfigured(message)

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

                # Remove from archived payload, virustotal and thug
                # now in root
                j.pop("payload", None)
                j.pop("virustotal", None)
                j.pop("thug", None)

            attachments.append(i)

        # Remove from mail the attachments huge fields like payload
        # Fetch from Elasticsearch more fast
        for i in mail.get("attachments", []):
            i.pop("payload", None)
            i.pop("tika", None)
            i.pop("virustotal", None)
            i.pop("thug", None)

            for j in i.get("files", []):
                j.pop("payload", None)
                j.pop("virustotal", None)
                j.pop("thug", None)

        # Prepair mail for bulk
        if bolt == "output-elasticsearch":
            mail["@timestamp"] = timestamp
            mail["_index"] = kwargs["elastic_index_mail"] + mail_date
            mail["type"] = kwargs["elastic_type_mail"]
            mail["_type"] = kwargs["elastic_type_mail"]

        return mail, attachments
