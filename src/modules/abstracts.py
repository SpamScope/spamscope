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
from abc import ABCMeta
import os

from streamparse.bolt import Bolt
from streamparse.spout import Spout

from .utils import load_config

try:
    # import for streamparse
    from options import __defaults__
except ImportError:
    # import for unittest
    from ..options import __defaults__

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap


# Constants mail types
MAIL_PATH = 0
MAIL_STRING = 1
MAIL_PATH_OUTLOOK = 2


class AbstractComponentMixin(object):

    __metaclass__ = ABCMeta

    _options = ChainMap(os.environ, __defaults__)

    def _conf_loader(self):
        self.log("Reloading configuration for {!r}".format(
            self.component_name))
        self._spamscope_conf = load_config(self.conf_file)

    @property
    def conf_file(self):
        return self.options["SPAMSCOPE_CONF_FILE"]

    @property
    def spamscope_conf(self):
        return self._spamscope_conf

    @property
    def conf(self):
        return self.spamscope_conf[self.component_name]

    @property
    def options(self):
        return self._options


class AbstractBolt(Bolt, AbstractComponentMixin):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        self._conf_loader()

    def process_tick(self, freq):
        """Every freq seconds you reload configuration """
        self._conf_loader()


class AbstractSpout(Spout, AbstractComponentMixin):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        self._conf_loader()
