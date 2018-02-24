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
import logging
import os

from simplejson import JSONDecodeError

try:
    from modules import register
except ImportError:
    from ...modules import register


processors = set()


log = logging.getLogger(__name__)


"""
This module contains all post processors for mail attachments
(i.e.: VirusTotal, Thug, etc.).

The skeleton of function must be like this:

    @register(processors, active=True)
    def processor(conf, attachments):
        if conf["enabled"]:
            from module_x import y # import custom object for this processor

            for a in attachments:
                # check if sample is filtered
                if not a.get("is_filtered", False):
                    pass

The function must be have the same name of configuration section in
conf/spamscope.yml --> attachments --> processor

The results will be added on attachments given as input.

Don't forget decorator @register()

You don't need anything else.
"""


@register(processors, active=True)
def tika(conf, attachments):
    """This method updates the attachments results
    with the Tika reports.

    Args:
        attachments (list): all attachments of email
        conf (dict): conf of this post processor

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        from tikapp import TikaApp
        tika = TikaApp(file_jar=conf["path_jar"],
                       memory_allocation=conf["memory_allocation"])

        for a in attachments:
            if not a.get("is_filtered", False):
                if a["Content-Type"] in conf["whitelist_content_types"]:
                    payload = a["payload"]

                    if a["content_transfer_encoding"] != "base64":
                        try:
                            payload = payload.encode("base64")
                        except UnicodeError:
                            # content_transfer_encoding': u'x-uuencode'
                            # it's not binary with strange encoding
                            continue

                    # tika-app only gets payload in base64
                    try:
                        a["tika"] = tika.extract_all_content(
                            payload=payload,
                            convert_to_obj=True)
                    except JSONDecodeError:
                        log.warning(
                            "JSONDecodeError for {!r} in Tika analysis".format(
                                a["md5"]))


@register(processors, active=True)
def virustotal(conf, attachments):
    """This method updates the attachments results
    with the Virustotal reports.

    Args:
        attachments (list): all attachments of email
        conf (dict): conf of this post processor

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        from virus_total_apis import PublicApi as VirusTotalPublicApi
        from .utils import reformat_virustotal

        vt = VirusTotalPublicApi(conf["api_key"])
        wtlist = conf["whitelist_content_types"]

        for a in attachments:
            if not a.get("is_filtered", False) and a["Content-Type"] in wtlist:
                # main/archive
                result = vt.get_file_report(a["sha1"])
                reformat_virustotal(result)
                if result:
                    a["virustotal"] = result

            # files in archive
            for i in a.get("files", []):
                if not i.get("is_filtered", False) \
                        and i["Content-Type"] in wtlist:
                    i_result = vt.get_file_report(i["sha1"])
                    reformat_virustotal(i_result)
                    if i_result:
                        i["virustotal"] = i_result


@register(processors, active=True)
def thug(conf, attachments):
    """This method updates the attachments results
    with the Thug reports.

    Args:
        attachments (list): all attachments of email
        conf (dict): conf of this post processor

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        from .thug_analysis import ThugAnalysis
        thug = ThugAnalysis()

        for a in attachments:
            if not a.get("is_filtered", False):
                if a["extension"] in conf["extensions"]:
                    a["thug"] = thug.run(a, **conf)

                for i in a.get("files", []):
                    if i["extension"] in conf["extensions"]:
                        i["thug"] = thug.run(i, **conf)


@register(processors, active=True)
def zemana(conf, attachments):
    """This method updates the attachments results
    with Zemana AntiMalware reports.

    Args:
        attachments (list): all attachments of email

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        try:
            from zemana import Zemana
        except ImportError:
            raise ImportError("Zemana library not found. You should be Zemana "
                              "customer (https://www.zemana.com/)")

        from requests.exceptions import HTTPError

        z = Zemana(int(conf["PartnerId"]), conf["UserId"],
                   conf["ApiKey"], conf["useragent"])

        for a in attachments:
            if not a.get("is_filtered", False):
                try:
                    result = z.query(a["md5"])
                except HTTPError:
                    log.exception(
                        "HTTPError in Zemana query for md5 {!r}".format(
                            a["md5"]))

                if result:
                    a["zemana"] = result.json
                    a["zemana"]["type"] = result.type

                for i in a.get("files", []):
                    try:
                        i_result = z.query(i["md5"])
                    except HTTPError:
                        log.exception(
                            "HTTPError in Zemana query for md5 {!r}".format(
                                i["md5"]))

                    if i_result:
                        i["zemana"] = i_result.json
                        i["zemana"]["type"] = i_result.type


@register(processors, active=True)
def store_samples(conf, attachments):
    """This method stores the attachments on file system.

    Args:
        attachments (list): all attachments of email
        conf (dict): conf of this post processor

    Returns:
        This method updates the attachments list given
    """

    if conf["enabled"]:
        from .utils import write_sample

        base_path = conf["base_path"]

        for a in attachments:
            if not a.get("is_filtered", False):

                # commons
                date_str = a["analisys_date"].split("T")[0]
                path = os.path.join(base_path, date_str)

                # do not write if has archived files
                if not a.get("files", []):
                    write_sample(
                        binary=a["binary"],
                        payload=a["payload"],
                        path=path,
                        filename=a["filename"],
                        hash_=a["md5"],
                    )

                # save file in archive
                for i in a.get("files", []):
                    write_sample(
                        # All archived files have base64 payload
                        binary=True,
                        payload=i["payload"],
                        path=path,
                        filename=i["filename"],
                        hash_=i["md5"],
                    )
