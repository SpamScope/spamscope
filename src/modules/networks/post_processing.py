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

from __future__ import absolute_import, print_function, unicode_literals

try:
    from modules import register
except ImportError:
    from ...modules import register


processors = set()


"""
This module contains all post processors for IP address
(i.e.: VirusTotal, Shodan.io, etc.).

The skeleton of function must be like this:

    @register(processors, active=True)
    def processor(conf, ipaddress, results):
        if conf["enabled"]:
            from module_x import y # import custom object for this processor
            ...

The function must be have the same name of configuration section in
conf/spamscope.yml --> network --> processor

The results will be added on dict given as input.

Don't forget decorator @register()

You don't need anything else.
"""


@register(processors, active=True)
def shodan(conf, ipaddress, results):
    """This method updates the attachments results
    with the Tika reports.

    Args:
        attachments (list): all attachments of email
        ipaddress (string): ip address to analyze
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        pass


@register(processors, active=True)
def virustotal(conf, ipaddress, results):
    """This method updates the attachments results
    with the Virustotal reports.

    Args:
        attachments (list): all attachments of email
        ipaddress (string): ip address to analyze
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        pass
