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
from tikapp import TikaApp
from virus_total_apis import PublicApi as VirusTotalPublicApi

processors = set()


def register(active=True):
    """Add processor to set of processors.
    From the best Python book Fluent Python (https://github.com/fluentpython).
    Thanks a lot Luciano Ramalho.
    """

    def decorate(func):
        if active:
            processors.add(func)
        else:
            processors.discard(func)

        return func

    return decorate


@register(active=True)
def tika(conf, attachments):
    """This method updates the attachments results
    with the Tika output.

    Args:
        attachments (list): all attachments of email

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        tika = TikaApp(file_jar=conf["path_jar"],
                       memory_allocation=conf["memory_allocation"])

        for a in attachments:
            if a['Content-Type'] in conf["whitelist_cont_types"]:
                a['tika'] = tika.extract_all_content(
                    payload=a['payload'], convert_to_obj=True)


@register(active=False)
def virustotal(conf, attachments):
    """This method updates the attachments results
    with the Virustotal report.

    Args:
        attachments (list): all attachments of email

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        vt = VirusTotalPublicApi(conf["api_key"])

        for a in attachments:
            print(a['sha1'])
            result = vt.get_file_report(a["sha1"])

            if result:
                a['virustotal'] = result

            for i in a.get("files", []):
                i_result = vt.get_file_report(i["sha1"])

                if i_result:
                    i['virustotal'] = i_result


@register(active=False)
def thug(configuration, attachments):
    pass
