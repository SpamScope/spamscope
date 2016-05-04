from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.mail_parser import MailParser


class Tokenizer(Bolt):
    outputs = ['message_id', 'mail']

    def process(self, tup):
        mail_path = tup.values[0]
        p = MailParser()
        p.parse_from_file(mail_path)
        mail = p.parsed_mail_json
        message_id = p.message_id
        self.emit([message_id, mail])
