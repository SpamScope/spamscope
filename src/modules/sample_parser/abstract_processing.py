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

from abc import ABCMeta, abstractmethod
from .exceptions import InvalidAttachment


class AbstractProcessing(object):

    __metaclass__ = ABCMeta

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._check_arguments()

    def __getattr__(self, name):
        try:
            return self._kwargs[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    def __setattr__(self, name, value):
        super(AbstractProcessing, self).__setattr__(name, value)

    @abstractmethod
    def process(self, attachments):
        if not isinstance(attachments, dict):
            raise InvalidAttachment("Attachment result is not a dict")

    @abstractmethod
    def _check_arguments(self):
        pass
