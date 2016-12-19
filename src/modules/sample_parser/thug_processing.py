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

import logging
import os
import tempfile
from .abstract_processing import AbstractProcessing
from .exceptions import MissingArgument, TempIOError
from ..thug_analysis import ThugAnalysis

log = logging.getLogger(__name__)


class ThugAnalysisFailed(Exception):
    pass


class ThugProcessing(AbstractProcessing):
    """ This class processes the output mail attachments to add
    Thug analysis.

    Args:
        referer (string): Referer to use for analysis
        extensions (list or set): list of extensions to analyze
        user_agents (list or set): list of user agents to use for analysis
    """

    def __init__(self, **kwargs):
        super(ThugProcessing, self).__init__(**kwargs)
        self._thug = ThugAnalysis()

    def _check_arguments(self):
        """
        This method checks if all mandatory arguments are given
        """

        if 'referer' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format('referer', type(self).__name__))

        if 'extensions' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format(
                'extensions', type(self).__name__))

        if 'user_agents' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format(
                'user_agents', type(self).__name__))

    def _write_attachment(self, payload, extension):
        """This method writes the attachment payload on file system in temporary file.

        Args:
            payload (string): binary payload string in base64 to write on disk
            extension (string): file extension. Example '.js'

        Returns:
            Local file path of payload
        """

        try:
            temp = tempfile.mkstemp()[1] + extension
            with open(temp, 'wb') as f:
                f.write(payload.decode('base64'))
            return temp
        except:
            raise TempIOError("Failed opening '{}' file".format(temp))

    def _single_analysis(self, sample):
        results = []
        local_file = self._write_attachment(
            sample['payload'], sample['extension'])

        # Thug analysis
        for u in self.user_agents:
            try:
                analysis = self._thug.analyze(local_file, u, self.referer)
                results.append(analysis)
            except:
                msg = "Thug analysis failed for sample sha1 '{}'".format(
                    sample['sha1'])
                log.error(msg)
                raise ThugAnalysisFailed(msg)

        try:
            os.remove(local_file)
        except:
            log.error("Failed removing '{}' temporary file".format(
                local_file))

        return results

    def process(self, attachment):
        """This method updates the attachment result
        with the Thug report.

        Args:
            attachment (dict): dict with a raw attachment mail

        Returns:
            This method updates the attachment dict given
        """
        super(ThugProcessing, self).process(attachment)

        if attachment['extension'] in self.extensions:
            attachment['thug'] = self._single_analysis(attachment)

        if attachment['is_archive']:
            for i in attachment['files']:
                if i['extension'] in self.extensions:
                    i['thug'] = self._single_analysis(i)
