from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.utils import search_words
import re
try:
    import simplejson as json
except ImportError:
    import json


class Phishing(Bolt):
    # TODO: Handling Tick Tuples reload keywords

    def initialize(self, conf, ctx):
        self.keywords = [
            "banca marche",
            "cartasi",
            "amazon",
            "dropbox",
            "aosta",
        ]

    def process(self, tup):
        sha256_random = tup.values[0]
        phishing = False

        try:
            mail = json.loads(tup.values[1])
            words_list = set(re.findall(r"[\w]+", mail.get("body")))

            if search_words(self.keywords, words_list):
                phishing = True
                self.log("Phishing for mail '{}'".format(sha256_random))

        except Exception as e:
            self.log(
                "Failed processing phishing for mail '{}".format(
                    sha256_random
                ),
                level="error"
            )
            self.raise_exception(e, tup)

        finally:
            self.emit([sha256_random, phishing])
