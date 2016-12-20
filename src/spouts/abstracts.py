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
import os
from streamparse.spout import Spout

from abc import ABCMeta
from modules.exceptions import ImproperlyConfigured
from modules.utils import load_config
from options import __defaults__

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap


class AbstractSpout(Spout):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        self._options = ChainMap(os.environ, __defaults__)
        self._conf_file = self.options['SPAMSCOPE_CONF_FILE']
        self._conf_loader()

    def _conf_loader(self):
        if not self.conf_file:
            raise ImproperlyConfigured(
                "Spouts configuration path NOT set for '{}'".format(
                    self.component_name))
        self.log("Reloading configuration for spout")
        self._spouts_conf = load_config(self.conf_file)
        self._conf = self.spouts_conf[self.component_name]

    @property
    def conf_file(self):
        return self._conf_file

    @property
    def spouts_conf(self):
        return self._spouts_conf

    @property
    def conf(self):
        return self._conf

    @property
    def options(self):
        return self._options

    def next_tuple(self):
        pass
