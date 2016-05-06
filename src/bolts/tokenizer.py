from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.mail_parser import MailParser
from modules.utils import fingerprints
import random

try:
    import simplejson as json
except ImportError:
    import json


class Tokenizer(Bolt):
    outputs = ['sha256_random', 'mail']

    def process(self, tup):
        try:
            mail_path = tup.values[0]

            # Parsing mail
            p = MailParser()
            p.parse_from_file(mail_path)
            mail = p.parsed_mail_obj

            # Fingerprints of body mail
            md5, sha1, sha256, sha512, ssdeep_ = fingerprints(
                p.body.encode('utf-8')
            )
            mail['md5'] = md5
            mail['sha1'] = sha1
            mail['sha256'] = sha256
            mail['sha512'] = sha512
            mail['ssdeep_'] = ssdeep_

            # Serialize mail
            mail_date = mail.get('date')
            if mail_date:
                mail['date'] = mail_date.isoformat()

            mail_json = json.dumps(
                mail,
                ensure_ascii=False,
            )

            # if two mails have the same sha256
            random_s = '_' + ''.join(
                random.choice('0123456789') for i in range(10)
            )

            self.emit([sha256 + random_s, mail_json])

        except Exception as e:
            self.log(
                "Failed parsing mail path: {}".format(mail_path),
                "error"
            )
            self.raise_exception(e, tup)
