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

import re
from virus_total_apis import PublicApi as VirusTotalPublicApi
from .abstract_processing import AbstractProcessing
from .exceptions import MissingArgument, VirusTotalApiKeyInvalid


class VirusTotalProcessing(AbstractProcessing):
    """ This class processes the output mail attachment to add
    VirusTotal report.

    Args:
        api_key (string): VirusTotal api key
    """

    def _check_arguments(self):
        """
        This method check if all mandatory arguments are given
        """

        if 'api_key' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format('api_key', type(self).__name__))

    def process(self, attachment):
        """This method updates the attachment result
        with the Virustotal report.

        Args:
            attachment (dict): dict with a raw attachment mail

        Returns:
            This method updates the attachment dict given
        """
        super(VirusTotalProcessing, self).process(attachment)

        if not self.api_key or not re.match(r'[a-z0-9]{64}', self.api_key):
            raise VirusTotalApiKeyInvalid("Add a valid VirusTotal API key!")

        vt = VirusTotalPublicApi(self.api_key)

        sha1 = attachment['sha1']
        result = vt.get_file_report(sha1)
        if result:
            attachment['virustotal'] = result

        if attachment['is_archive']:
            for i in attachment['files']:
                i_sha1 = i['sha1']
                i_result = vt.get_file_report(i_sha1)
                if i_result:
                    i['virustotal'] = i_result
