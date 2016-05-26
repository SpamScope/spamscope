"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from __future__ import absolute_import, print_function, unicode_literals
from streamparse.bolt import Bolt

import os

try:
    import simplejson as json
except ImportError:
    import json


class OutputDebug(Bolt):
    """ Output tokenized mails on files. """

    def initialize(self, conf, ctx):
        self.output_path = "/tmp/mails"

        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def process(self, tup):
        try:
            sha256_random = tup.values[0]
            mail = json.dumps(
                json.loads(tup.values[1]),
                ensure_ascii=False,
                indent=4,
            )

            with open(
                os.path.join(
                    self.output_path,
                    "{}.json".format(sha256_random)
                ),
                "w"
            ) as f:
                f.write(mail.encode('utf-8'))

        except Exception as e:
            self.log(
                "Failed process json for mail: {}".format(sha256_random),
                "error"
            )
            self.raise_exception(e, tup)
