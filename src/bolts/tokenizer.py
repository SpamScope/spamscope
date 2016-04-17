from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.mail_parser import MailParser


class Tokenizer(Bolt):

    def process(self, tup):
        mail_path = tup.values[0]
        self.log('Mail in analysis: {}'.format(mail_path), 'info')
        p = MailParser()
        p.parse_from_file(mail_path)
        self.emit(
            [
                mail_path,
                p.parsed_mail_json,
            ]
        )
