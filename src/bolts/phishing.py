from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from pyparsing import oneOf
import json


class Phishing(Bolt):

    def initialize(self, conf, ctx):
        self.parser_ = oneOf('intesa cartasi marche')('phishing')

    def process(self, tup):
        mail_path = tup.values[0]
        mail = json.loads(tup.values[1])

        results = self.parser_.searchString(mail["body"])
        if results:
            r_string = ""
            for i in results.asList():
                r_string += i[0] + " "
            r_string = r_string.strip()

            # self.log(
                # "Path: {}. Matchs: {}".format(
                    # mail_path,
                    # r_string,
                # )
            # )
        self.emit([mail_path])
