#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os.path import join

__version__ = "v1.4.1"
__configuration_path__ = "/etc/spamscope"

__defaults__ = {
    "SPAMSCOPE_CONF_PATH": __configuration_path__,
    "SPAMSCOPE_CONF_FILE": join(__configuration_path__, "spamscope.yml"),
    "SPAMSCOPE_VER": __version__, }
