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

from .bitmap import BitMap


class PhishingBitMap(BitMap):
    """This map assigns a phishing score to the mail.
    Range from 0 (no phishing) to 127 (high probability).
    """

    _map_name = "phishing_bitmap"

    def define_bitmap(self):
        self._bitmap = {
            "mail_body": 0,
            "urls_body": 1,
            "text_attachments": 2,
            "urls_attachments": 3,
            "filename_attachments": 4,
            "mail_from": 5,
            "mail_subject": 6,
            "mail_form": 7}
