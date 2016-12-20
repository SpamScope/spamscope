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
from streamparse.bolt import Bolt

from abc import ABCMeta
from datetime import datetime
from modules.exceptions import ImproperlyConfigured
from modules.urls_extractor import UrlsExtractor
from modules.utils import load_config
from src import __defaults__

try:
    import simplejson as json
except ImportError:
    import json

try:
    from collections import ChainMap
except ImportError:
    from chainmap import ChainMap


class AbstractBolt(Bolt):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        self._options = ChainMap(os.environ, __defaults__)
        self._conf_file = self.options['SPAMSCOPE_CONF_FILE']
        self._conf_loader()

    def _conf_loader(self):
        if not self.conf_file:
            raise ImproperlyConfigured(
                "Bolts configuration path NOT set for '{}'".format(
                    self.component_name))
        self.log("Reloading configuration for bolt")
        self._bolts_conf = load_config(self.conf_file)
        self._conf = self.bolts_conf[self.component_name]

    def process_tick(self, freq):
        """Every freq seconds you reload configuration """
        self._conf_loader()

    @property
    def conf_file(self):
        return self._conf_file

    @property
    def bolts_conf(self):
        return self._bolts_conf

    @property
    def conf(self):
        return self._conf

    @property
    def options(self):
        return self._options

    def process(self):
        pass


class AbstractUrlsHandlerBolt(AbstractBolt):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        super(AbstractUrlsHandlerBolt, self).initialize(stormconf, context)
        self._extractor = UrlsExtractor()
        self._load_whitelist()

    def _load_whitelist(self):

        self.log("Reloading whitelists domains for bolt")
        self._whitelist = set()
        for k, v in self.conf['whitelists'].iteritems():
            expiry = v.get('expiry')
            now = datetime.utcnow()

            if (not expiry or
                    datetime.strptime(expiry, "%Y-%m-%dT%H:%M:%S.%fZ") >= now):
                domains = load_config(v['path'])

                if not isinstance(domains, list):
                    raise ImproperlyConfigured(
                        "Whitelist {} not loaded".format(k)
                    )
                domains = [i.lower() for i in domains]
                self._whitelist |= set(domains)
                self.log("Whitelist '{}' loaded".format(k))

    def process_tick(self, freq):
        """Every freq seconds you reload the whitelist """
        super(AbstractUrlsHandlerBolt, self).process_tick(freq)
        self._load_whitelist()

    def _extract_urls(self, text, conv_to_str=True):
        with_urls = False
        urls = dict()

        if text:
            self._extractor.extract(text)
            urls = self._extractor.urls_obj
            domains = urls.keys()

            for d in domains:
                if d.lower() in self._whitelist:
                    urls.pop(d)

        if urls:
            with_urls = True

        if conv_to_str:
            urls = json.dumps(urls, ensure_ascii=False)

        return with_urls, urls
