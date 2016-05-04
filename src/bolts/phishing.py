from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

from modules.utils import search_words
import re
try:
    import simplejson as json
except:
    import json


class Phishing(Bolt):
    outputs = ['message_id', 'phishing']

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
        message_id = tup.values[0]
        mail = json.loads(tup.values[1])
        words_list = re.findall(r"[\w]+", mail.get("body"))
        phishing = False

        if search_words(self.keywords, words_list):
            phishing = True
        self.emit([message_id, phishing])
