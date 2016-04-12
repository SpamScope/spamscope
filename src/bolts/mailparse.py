from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

import email


class MailParser(Bolt):

    def process(self, tup):
        message = email.message_from_string(tup.values[0].decode('base64'))

        for i in message.walk():
            if not i.is_multipart():
                self.log("Mime type: {}".format(i.get_content_type()))
                content_type = i.get('content-transfer-encoding', '')
                self.log("Content type: {}".format(content_type))
