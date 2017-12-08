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

from __future__ import unicode_literals
import email
import logging
import os
import re
import subprocess

from astropy.io import ascii
import six


log = logging.getLogger(__name__)


def obj_report(s):
    """This function parses the new mail with extra report of spamassassin
    and return a Python object with only spamassassin report

    Args:
        s (string): new mail with extra report

    Returns:
        Python object with spamassassin report
    """

    SCORE_REGX = re.compile(r"score=([0-9\.]+)")
    s = six.text_type(s, encoding="ascii", errors="ignore")

    message = email.message_from_string(s)

    try:
        t = message.epilogue
        t = t[t.index("pts rule name"):].strip()
    except (ValueError, AttributeError):
        return {}

    details = convert_ascii2json(t)
    spam_checker_version = message.get("X-Spam-Checker-Version")
    spam_flag = message.get("X-Spam-Flag")
    spam_level = message.get("X-Spam-Level")
    spam_status = message.get("X-Spam-Status")

    try:
        score = float(SCORE_REGX.search(spam_status).group(1))
    except AttributeError:
        score = 0.0

    report = {
        "X-Spam-Checker-Version": spam_checker_version,
        "X-Spam-Flag": spam_flag,
        "X-Spam-Level": spam_level,
        "X-Spam-Status": spam_status,
        "score": score,
        "details": details}

    return report


def report_from_file(fp):
    """This function parses the new mail with extra report of spamassassin
    and return a Python object with only spamassassin report

    Args:
        fp (string): mail path

    Returns:
        Python object with spamassassin report
    """

    mail = analysis_from_file(fp)
    return obj_report(mail)


def analysis_from_file(fp):
    """This function analyzes the file mail with 'spamassassin -t' command
    and return a new mail with extra report and headers.

    Args:
        fp (string): mail path

    Returns:
        new mail (string): mail with extra report and headers
    """

    command = ["spamassassin", "-t", fp]

    if six.PY2:
        with open(os.devnull, "w") as devnull:
            out = subprocess.Popen(
                command, stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, stderr=devnull)
    elif six.PY3:
        out = subprocess.Popen(
            command, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    stdoutdata, _ = out.communicate()
    return stdoutdata


def report_from_string(s):
    raise NotImplementedError("function not implemented")


def convert_ascii2json(table):
    """This function converts the ASCII table report of spamassassin in
    a Python object

    Args:
        table (string): ASCII table

    Returns:
        spamassassin report as Python object
    """

    t = ascii.read(table, fill_values=(''))
    l = []

    for row in t:
        if row[0] or row[0] == 0:
            l.append({
                "pts": float(row[0]),
                "rule name": row[1].strip(),
                "description": row[2].strip()})
        else:
            if row[1]:
                l[-1]["rule name"] += " " + row[1].strip()
            if row[2]:
                l[-1]["description"] += " " + row[2].strip()
    else:
        return l
