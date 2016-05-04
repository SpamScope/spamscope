from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from lxml import html
try:
    import simplejson as json
except:
    import json


class Forms(Bolt):
    outputs = ['message_id', 'forms']

    def process(self, tup):
        message_id = tup.values[0]
        mail = json.loads(tup.values[1])
        forms = False
        body = mail.get('body')

        if body:
            try:
                tree = html.fromstring(body)
                results = tree.xpath('//form')
                if results:
                    forms = True
            except:
                self.log("Failed parsing body part", level="warn")

        self.emit([message_id, forms])
