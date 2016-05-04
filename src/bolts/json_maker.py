from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

try:
    import simplejson as json
except:
    import json


class JsonMaker(Bolt):

    def initialize(self, storm_conf, context):
        self.mails = {}
        self.input_bolts = set([
            "tokenizer-bolt",
            "phishing-bolt",
            "attachments-bolt",
            "forms-bolt",
        ])

    def _compose_output(self, greedy_data):
        mail = json.loads(greedy_data['tokenizer-bolt'][1])
        mail['with_phishing'] = greedy_data['phishing-bolt'][1]
        mail['with_forms'] = greedy_data['forms-bolt'][1]
        mail['with_attachments'] = greedy_data['attachments-bolt'][1]
        if mail['with_attachments']:
            mail['attachments'] = json.loads(
                greedy_data['attachments-bolt'][2]
            )

        return json.dumps(
            mail,
            indent=4,
            ensure_ascii=False,
        )

    def process(self, tup):
        bolt = tup.component
        message_id = tup.values[0]
        values = tup.values

        if self.mails.get(message_id, None):
            self.mails[message_id][bolt] = values
        else:
            self.mails[message_id] = {bolt: values}

        diff = self.input_bolts - set(self.mails[message_id].keys())

        if not diff:
            self.log("JSON for mail '{}'".format(message_id))
            output_json = self._compose_output(self.mails[message_id])

            with open("/tmp/mails/{}.json".format(message_id), "w") as f:
                f.write(output_json.encode('utf-8'))
