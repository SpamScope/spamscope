from __future__ import absolute_import, print_function, unicode_literals
from streamparse.spout import Spout

import glob
import os


class MailSpout(Spout):

    def initialize(self, stormconf, context):
        mails_path = '/home/fedelemantuano/Desktop/mails/'
        # TODO: get from QueueItem
        self._mails_iglob = glob.iglob(os.path.join(mails_path, '*heidi*'))

    def next_tuple(self):
        for i in self._mails_iglob:
            with open(i) as mail:
                self.emit([mail.read().encode('base64')])
