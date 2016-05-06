from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from lxml import html
try:
    import simplejson as json
except ImportError:
    import json


class Forms(Bolt):
    outputs = ['sha256_random', 'forms']

    def process(self, tup):
        sha256_random = tup.values[0]
        forms = False

        try:
            mail = json.loads(tup.values[1])
            body = mail.get('body')

            if body.strip():
                tree = html.fromstring(body)
                results = tree.xpath('//form')
                if results:
                    forms = True
                    self.log("Forms for mail '{}'".format(sha256_random))

        except Exception as e:
            self.log(
                "Failed parsing body part for mail '{}".format(sha256_random),
                level="error"
            )
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_random, forms])
