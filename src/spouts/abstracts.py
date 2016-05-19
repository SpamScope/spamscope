from __future__ import absolute_import, print_function, unicode_literals
from streamparse.spout import Spout

from abc import ABCMeta
from modules.exceptions import ImproperlyConfigured
from modules.utils import load_config


class AbstractSpout(Spout):

    __metaclass__ = ABCMeta

    def initialize(self, stormconf, context):
        self._conf_file = stormconf.get("spouts.conf", None)
        self._spout_conf_loader()

    def _spout_conf_loader(self):
        if not self.conf_file:
            raise ImproperlyConfigured(
                "Spouts configuration path NOT set for '{}'".format(
                    self.component_name
                )
            )
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

    def next_tuple(self):
        pass
