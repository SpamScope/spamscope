#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
from modules import AbstractBolt

import os

try:
    import simplejson as json
except ImportError:
    import json


class OutputDebug(AbstractBolt):
    """Output tokenized mails on files. """

    def initialize(self, stormconf, context):
        super(OutputDebug, self).initialize(stormconf, context)
        self._json_indent = self.conf["json.indent"]
        self._output_path = self.conf["output.path"]

        if not os.path.exists(self._output_path):
            os.makedirs(self._output_path)

    def process(self, tup):
        sha256_random = tup.values[0]
        mail = json.dumps(tup.values[1], ensure_ascii=False,
                          indent=self._json_indent)

        output = os.path.join(self._output_path, "{}.json".format(
            sha256_random))

        with open(output, "w") as f:
            f.write(mail.encode('utf-8'))
