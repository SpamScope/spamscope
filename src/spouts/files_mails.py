#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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
from datetime import date

import Queue
import glob
import os
import shutil

import six

from modules import (
    AbstractSpout,
    MAIL_PATH,
    MAIL_PATH_OUTLOOK,
    MailItem,
    is_file_older_than,
)


class FilesMailSpout(AbstractSpout):
    outputs = ['raw_mail', 'mail_server', 'mailbox',
               'priority', 'trust', 'mail_type', 'headers']

    def initialize(self, stormconf, context):
        super(FilesMailSpout, self).initialize(stormconf, context)
        self._check_conf()
        self._queue = Queue.PriorityQueue()
        self._count = 1
        self._load_mails()

    def _move_fail(self, src):
        mail_string = src.split("/")[-1]
        mail = os.path.join(self._where_failed, mail_string)
        processing = src + ".processing"

        try:
            os.chmod(processing, 0o775)
            shutil.move(processing, mail)
        finally:
            self.log("FAILED - {!r}".format(mail_string))

    def _check_conf(self):
        self._fail_seconds = int(self.conf.get("fail.after.seconds", 60))
        self._what = self.conf["post_processing"].get("what", "remove").lower()
        self._where = self.conf["post_processing"].get("where", "/tmp/moved")
        if not os.path.exists(self._where):
            os.makedirs(self._where)
        self._where_failed = self.conf["post_processing"].get(
            "where.failed", "/tmp/failed")
        if not os.path.exists(self._where_failed):
            os.makedirs(self._where_failed)

    def _fail_old_mails(self, processing_mails):
        for i in processing_mails:
            mail = i.replace(".processing", "")
            mail_string = mail.split("/")[-1]
            if is_file_older_than(i, self._fail_seconds):
                self.log("Mail {!r} older than {} seconds".format(
                    mail_string, self._fail_seconds))
                self._move_fail(mail)

    def _load_mails(self):
        """This function load mails in a priority queue. """
        self.log("Loading new mails for {!r}".format(self.component_name))

        for k, v in self.conf["mailboxes"].iteritems():
            all_mails = set(glob.glob(os.path.join(
                v["path_mails"], v["files_pattern"])))
            processing_mails = set(glob.glob(os.path.join(
                v["path_mails"], "*.processing")))

            # put new mails in queue
            for mail in (all_mails - processing_mails):
                mail_type = MAIL_PATH_OUTLOOK \
                    if v.get("outlook", False) else MAIL_PATH

                self._queue.put(
                    MailItem(
                        filename=mail,
                        mail_server=v["mail_server"],
                        mailbox=k,
                        priority=v["priority"],
                        trust=v["trust_string"],
                        mail_type=mail_type,
                        headers=v.get("headers", [])))

            # Fail old mails
            self._fail_old_mails(processing_mails)

    def next_tuple(self):
        # After reload.mails next_tuple reload spout config
        if (self._count % self.conf["reload.mails"]):
            self._count += 1

        # put new mails in priority queue
        else:
            # Reload general spout conf
            self._conf_loader()

            # Reload new mails
            self._load_mails()
            self._count = 1

        # If queue is not empty
        if not self._queue.empty():
            mail = self._queue.get(block=True)

            mail_string = mail.filename.split("/")[-1]
            self.log("EMITTED - {!r}".format(mail_string))

            processing = mail.filename + ".processing"

            try:
                shutil.move(mail.filename, processing)
            except IOError:
                self.log("ALREADY EMITTED - {!r}".format(mail_string))
            else:
                self.emit([
                    processing,  # 0
                    mail.mail_server,  # 1
                    mail.mailbox,  # 2
                    mail.priority,  # 3
                    mail.trust,  # 4
                    mail.mail_type,  # 5
                    mail.headers],  # 6
                    tup_id=mail.filename)

    def ack(self, tup_id):
        """Acknowledge tup_id, that is the path_mail. """
        self._queue.task_done()

        mail_string = tup_id.split("/")[-1]
        self.log("ACKED - {!r}".format(mail_string))

        processing = tup_id + ".processing"

        if self._what == "remove":
            try:
                os.remove(processing)
            except Exception:
                self.log("Failed to remove {!r} mail".format(processing))
        else:
            try:
                now = six.text_type(date.today())
                mail_path = os.path.join(self._where, now)
                if not os.path.exists(mail_path):
                    os.makedirs(mail_path)
                # this chmod is useful to work under
                # nginx directory listing
                os.chmod(processing, 0o775)
                mail = os.path.join(mail_path, mail_string)
                shutil.move(processing, mail)
            except shutil.Error:
                os.remove(processing)

    def fail(self, tup_id):
        try:
            self._queue.task_done()
        except ValueError:  # ValueError: task_done() called too many times
            pass
        finally:
            self._move_fail(tup_id)
