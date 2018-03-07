#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

from os.path import join

__version__ = "2.3.0"
__configuration_path__ = "/etc/spamscope"

__defaults__ = {
    "SPAMSCOPE_CONF_PATH": __configuration_path__,
    "SPAMSCOPE_CONF_FILE": join(__configuration_path__, "spamscope.yml"),
    "SPAMSCOPE_VER": __version__, }

if __name__ == "__main__":
    print(__version__)
