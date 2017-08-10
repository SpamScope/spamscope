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
import logging

import simplejson as json

try:
    from modules import register
except ImportError:
    from ...modules import register


processors = set()


log = logging.getLogger(__name__)


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
    """This method updates the network results
    with the Shodan report.

    Args:
        conf (dict): dict of configuration
        ipaddress (string): ip address to analyze
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        import shodan
        api = shodan.Shodan(conf["api_key"])

        try:
            r = api.host(ipaddress)
            report = json.dumps(r, ensure_ascii=False)
        except shodan.APIError:
            return
        except TypeError:
            log.error("JSON TypeError in Shodan report for ip {!r}".format(
                ipaddress))
        else:
            if report:
                results["shodan"] = report


@register(processors, active=True)
def virustotal(conf, ipaddress, results):
    """This method updates the network results
    with the Virustotal reports.

    Args:
        conf (dict): dict of configuration
        ipaddress (string): ip address to analyze
        results (dict): dict where will put the results

    Returns:
        This method updates the results dict given
    """

    if conf["enabled"]:
        from virus_total_apis import PublicApi as VirusTotalPublicApi
        vt = VirusTotalPublicApi(conf["api_key"])

        # Error: {u'virustotal': {'error': SSLError(SSLEOFError(8, u'EOF
        # occurred in violation of protocol (_ssl.c:590)'),)}}')
        # TypeError: SSLError(SSLEOFError(8, u'EOF occurred in violation of
        # protocol (_ssl.c:590)'),) is not JSON serializable')
        try:
            r = vt.get_ip_report(ipaddress)
            report = json.dumps(r, ensure_ascii=False)
        except TypeError:
            log.error("TypeError in VirusTotal report for ip {!r}".format(
                ipaddress))
        else:
            if report:
                results["virustotal"] = report
