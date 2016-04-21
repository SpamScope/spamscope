from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from lxml import html
import json


class Forms(Bolt):

    def process(self, tup):
        mail_path = tup.values[0]
        mail = json.loads(tup.values[1])
        forms = False
        body = mail.get('body', None)

        if body:
            try:
                tree = html.fromstring(body)
                results = tree.xpath('//form')
                if results:
                    forms = True
            except:
                self.log("Failed parsing body part", level="error")

        if forms:
            self.log("Path: {}, Forms: {}".format(mail_path, forms))

        self.emit([mail_path, forms])
