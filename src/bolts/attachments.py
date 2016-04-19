from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.utils import fingerprints

import json


class Attachments(Bolt):

    def process(self, tup):
        mail_path = tup.values[0]
        mail = json.loads(tup.values[1])

        attachments_json = None
        with_attachment = False
        attachments = mail.get('attachments', None)

        if attachments:
            for a in attachments:
                md5, sha1, sha256, sha512, ssdeep_ = fingerprints(
                    a["payload"].decode('base64')
                )
                a['md5'] = md5
                a['sha1'] = sha1
                a['sha256'] = sha256
                a['sha512'] = sha512
                a['ssdeep'] = ssdeep_

            attachments_json = json.dumps(
                attachments,
                ensure_ascii=False,
            )

            with_attachment = True

        if with_attachment:
            self.log(
                "Path: {}, Attachment: {}".format(mail_path, with_attachment)
            )

        self.emit([mail_path, with_attachment, attachments_json])
