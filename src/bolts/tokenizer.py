from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.parse_mail import ParseMail


class Tokenizer(Bolt):

    def process(self, tup):
        mail_path = tup.values[0]
        self.log('Mail in analysis: {}'.format(mail_path), 'info')
        p = ParseMail()
        p.parse_from_file(mail_path)
        self.emit(
            [
                mail_path,
                p.parsed_mail_json,
            ]
        )
