from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt


class OutputDebug(Bolt):

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            mail = tup.values[1]

            with open("/tmp/mails/{}.json".format(sha256_random), "w") as f:
                f.write(mail.encode('utf-8'))

        except Exception as e:
            self.log(
                "Failed process json for mail: {}".format(sha256_random),
                "error"
            )
            self.raise_exception(e, tup)
