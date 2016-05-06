from __future__ import absolute_import, print_function, unicode_literals
from streamparse.spout import Spout

import glob
import os
import time


class MailSpout(Spout):
    outputs = ['mail_path']

    def initialize(self, stormconf, context):
        mails_path = '/home/fedelemantuano/Desktop/mails/test'
        # TODO: get from QueueItem
        self._mails_iglob = glob.iglob(os.path.join(mails_path, '*heidi*'))

    def next_tuple(self):
        for i in self._mails_iglob:
            self.emit([i])
            time.sleep(0.1)
