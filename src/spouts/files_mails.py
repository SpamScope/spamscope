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

from __future__ import absolute_import, print_function, unicode_literals

import Queue
import glob
import os
import shutil
import time
from spouts.abstracts import AbstractSpout
from modules.errors import ImproperlyConfigured
from modules.utils import MailItem


MAIL_PATH = "path"


class FilesMailSpout(AbstractSpout):
    outputs = [
        'mail_path',
        'mail_server',
        'mailbox',
        'priority',
        'kind_data',
    ]

    def initialize(self, stormconf, context):
        super(FilesMailSpout, self).initialize(stormconf, context)

        self.queue = Queue.PriorityQueue()
        self.queue_tail = set()
        self.queue_fail = list()
        self.count = 1
        self.load_mails()
        self.waiting_sleep = float(self.conf["waiting.sleep"])
        self.max_retry = int(self.conf["max.retry"])

    def load_mails(self):
        """This function load mails in a priority queue. """

        self.log("Loading new mails for spout")

        mailboxes = self.conf['mailboxes']
        for k, v in mailboxes.iteritems():
            if not os.path.exists(v['path_mails']):
                raise ImproperlyConfigured(
                    "Mail path '{}' does NOT exist".format(v['path_mails'])
                )

            all_mails = set(glob.glob(os.path.join(
                v['path_mails'], '{}'.format(v['files_pattern']))))

            # put new mails in queue
            for mail in (all_mails - self.queue_tail):
                self.queue_tail.add(mail)
                self.queue.put(
                    MailItem(
                        filename=mail,
                        mail_server=v['mail_server'],
                        mailbox=k,
                        priority=v['priority'],
                    )
                )

    def next_tuple(self):

        # If queue is not empty
        if not self.queue.empty():

            # After reload.mails mails put new items in priority queue
            if (self.count % self.conf['reload.mails']):
                self.count += 1
                mail = self.queue.get(block=True)
                self.emit(
                    [
                        mail.filename,
                        mail.mail_server,
                        mail.mailbox,
                        mail.priority,
                        MAIL_PATH,
                    ],
                    tup_id=mail.filename,
                )

            # put new mails in priority queue
            else:
                # Reload general spout conf
                self._conf_loader()

                # Reload new mails
                self.load_mails()
                self.count = 1

        # If queue is empty
        else:
            self.log("Queue mails is empty")
            time.sleep(self.waiting_sleep)
            self.load_mails()

    def ack(self, tup_id):
        """Acknowledge tup_id, that is the path_mail. """

        self.queue.task_done()
        failed_tup = False

        try:
            # Remove from tail analyzed mail
            self.queue_tail.remove(tup_id)

            # Mark as failed
            if self.queue_fail.count(tup_id) >= self.max_retry:
                self.log("Tuple failed '{}' acked".format(tup_id))
                failed_tup = True

            # Remove from failed queue
            self.queue_fail = [i for i in self.queue_fail if i != tup_id]

            self.log("Mails to process: {}".format(len(self.queue_tail)))
            self.log("Mails in failed queue: {}".format(
                len(set(self.queue_fail))))

        except KeyError:
            pass

        # Mails post processing
        what = self.conf["post_processing"]["what"].lower()

        if what == "remove" and not failed_tup:
            # Delete mail if exists
            if os.path.exists(tup_id):
                os.remove(tup_id)

        elif what == "move" or (what == "remove" and failed_tup):
            if failed_tup:
                where = self.conf["post_processing"]["where.failed"]
            else:
                where = self.conf["post_processing"]["where"]

            if not where:
                raise ImproperlyConfigured(
                    "where or where.failed in '{}' is NOT configurated".format(
                        self.spouts_conf))

            # if path does not exist, do it
            if not os.path.exists(where):
                os.makedirs(where)

            # Try to move file
            try:
                shutil.move(tup_id, where)
            except shutil.Error as e:
                self.raise_exception(e)

        else:
            self.error("Error in spout conf. 'what' can be move or remove")

    def fail(self, tup_id):
        # If tuple fail the mail remains on disk, self.queue is empty but
        # self.queue_tail contains all failed tuples

        nr_fail = self.queue_fail.count(tup_id)

        if nr_fail < self.max_retry:

            # Returns in queue
            self.queue_tail.remove(tup_id)

            # Add in fail queue
            self.queue_fail.append(tup_id)
            self.log("Tuple '{}' fail for {} times".format(
                tup_id, nr_fail + 1), "warning")
        else:
            self.log("Tuple '{}' failed for {} times".format(
                tup_id, self.max_retry))

            # Remove from topology
            self.ack(tup_id)
