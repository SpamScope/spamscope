from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.utils import fingerprints

try:
    import simplejson as json
except ImportError:
    import json


class Attachments(Bolt):
    outputs = ['sha256_random', 'with_attachments', 'attachments_json']

    def process(self, tup):
        sha256_mail_random = tup.values[0]
        with_attachments = False
        attachments_json = None

        try:
            mail = json.loads(tup.values[1])
            attachments = mail.get('attachments', [])

            if attachments:
                with_attachments = True
                self.log(
                    "Attachments for mail '{}'".format(sha256_mail_random)
                )

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

        except Exception as e:
            self.log(
                "Failed process attachments for mail: {}".format(
                    sha256_mail_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_mail_random, with_attachments, attachments_json])
