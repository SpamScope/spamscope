from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.utils import fingerprints

try:
    import simplejson as json
except:
    import json


class Attachments(Bolt):
    outputs = ['message_id', 'with_attachments', 'attachments_json']

    def process(self, tup):
        message_id = tup.values[0]
        mail = json.loads(tup.values[1])
        attachments = mail.get('attachments', [])
        with_attachments = False
        attachments_json = None

        if attachments:
            with_attachments = True

            for a in attachments:
                md5, sha1, sha256, sha512, ssdeep_ = fingerprints(
                    a["payload"].decode('base64')
                )
                a['md5'] = md5
                a['sha1'] = sha1
                a['sha256'] = sha256
                a['sha512'] = sha512
                a['ssdeep'] = ssdeep_

                # TODO: check on virustotal

            attachments_json = json.dumps(
                attachments,
                ensure_ascii=False,
            )

        self.emit([message_id, with_attachments, attachments_json])
