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

from tikapp import TikaApp
from .abstract_processing import AbstractProcessing
from .exceptions import InvalidContentTypes, MissingArgument


class TikaProcessing(AbstractProcessing):
    """ This class processes the output mail attachments to add
    Apache Tika analysis.

    Args:
        jar (string): path of Apache Tika App jar
        valid_content_types (list or set): list of contents types to analyze
        memory_allocation (string): memory to give to Apache Tika App
    """

    def __init__(self, **kwargs):
        super(TikaProcessing, self).__init__(**kwargs)

        # Init Tika
        self._tika_client = TikaApp(
            file_jar=self.jar,
            memory_allocation=self.memory_allocation)

    def __getattr__(self, name):
        try:
            return self._kwargs[name]
        except KeyError:
            # Default values
            if name in ("memory_allocation"):
                return None
            else:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError(msg.format(type(self).__name__, name))

    def __setattr__(self, name, value):
        super(TikaProcessing, self).__setattr__(name, value)

        if name == "valid_content_types":
            if not isinstance(value, set) and not isinstance(value, list):
                raise InvalidContentTypes("Content types must be set or list")

            self._kwargs[name] = value

    def _check_arguments(self):
        """This method checks if all mandatory arguments are given. """

        if 'jar' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format('jar', type(self).__name__))

        if 'valid_content_types' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format(
                'valid_content_types', type(self).__name__))

    def process(self, attachment):
        """This method updates the attachment result
        with the Tika output.

        Args:
            attachment (dict): dict with a raw attachment mail

        Returns:
            This method updates the attachment dict given
        """

        super(TikaProcessing, self).process(attachment)

        if attachment['Content-Type'] in self.valid_content_types:
            attachment['tika'] = self._tika_client.extract_all_content(
                payload=attachment['payload'],
                convert_to_obj=True)
