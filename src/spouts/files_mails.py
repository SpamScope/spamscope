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


class FilesMailSpout(AbstractSpout):

    def initialize(self, stormconf, context):
        super(FilesMailSpout, self).initialize(stormconf, context)

        self.queue = Queue.PriorityQueue()
        self.queue_tail = set()
        self.count = 1
        self.load_mails()

    def load_mails(self):
        """This function load mails in a priority queue. """

        mailboxes = self.conf['mailboxes']

        for k, v in mailboxes.iteritems():

            if not os.path.exists(v['path_mails']):
                raise ImproperlyConfigured(
                    "Mail path '{}' does NOT exist".format(v['path_mails'])
                )

            all_mails = set(
                glob.glob(
                    os.path.join(
                        v['path_mails'],
                        '*{}*'.format(v['file_key']),
                    )
                )
            )
            new_mails = all_mails - self.queue_tail

            # put new mails in queue
            for mail in new_mails:
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
                    ],
                    tup_id=mail.filename,
                )
            # put new mails in priority queue
            else:
                self.load_mails()
                self.count = 1
        else:
            # Wait for new mails
            self.log("Queue mails is empty")
            time.sleep(1)
            self.load_mails()

    def ack(self, tup_id):
        """Acknowledge tup_id, that is the path_mail. """

        self.queue.task_done()

        try:
            # Remove from tail analyzed mail
            self.queue_tail.remove(tup_id)
            self.log("Mails to process: {}".format(len(self.queue_tail)))
        except KeyError:
            pass

        # Mails post processing
        what = self.conf["post_processing"]["what"].lower()

        if what == "remove":
            # Delete mail if exists
            if os.path.exists(tup_id):
                os.remove(tup_id)

        else:
            where = self.conf["post_processing"]["where"]
            if not where:
                raise ImproperlyConfigured(
                    "Path where in '{}' is NOT configurated".format(
                        self.spouts_conf
                    )
                )

            # if path does not exist, do it
            if not os.path.exists(where):
                os.makedirs(where)

            # Try to move file
            try:
                shutil.move(tup_id, where)
            except shutil.Error as e:
                self.raise_exception(e)
