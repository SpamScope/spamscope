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

import hashlib
import logging
import os
import patoolib
import ssdeep
import tempfile

log = logging.getLogger(__name__)


class Base64Error(ValueError):
    pass


class FailedTempIO(Exception):
    pass


class SampleParser(object):

    def fingerprints_from_base64(self, data):
        """This function return the fingerprints of data:
            - md5
            - sha1
            - sha256
            - sha512
            - ssdeep
        """

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.fingerprints(data)

    def fingerprints(self, data):
        """This function return the fingerprints of data:
            - md5
            - sha1
            - sha256
            - sha512
            - ssdeep
        """

        # md5
        md5 = hashlib.md5()
        md5.update(data)
        md5 = md5.hexdigest()

        # sha1
        sha1 = hashlib.sha1()
        sha1.update(data)
        sha1 = sha1.hexdigest()

        # sha256
        sha256 = hashlib.sha256()
        sha256.update(data)
        sha256 = sha256.hexdigest()

        # sha512
        sha512 = hashlib.sha512()
        sha512.update(data)
        sha512 = sha512.hexdigest()

        # ssdeep
        ssdeep_ = ssdeep.hash(data)

        return md5, sha1, sha256, sha512, ssdeep_

    def is_archive_from_base64(self, data):
        """This function return True if data is a archive, else False."""

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.is_archive(data)

    def is_archive(self, data):
        """This function return True if data is a archive, else False."""

        archive = True
        try:
            temp = tempfile.mkstemp()[1]
            with open(temp, 'wb') as f:
                f.write(data)
        except:
            raise FailedTempIO("Failed opening '{}' file".format(temp))

        try:
            patoolib.test_archive(temp)
        except:
            archive = False
        finally:
            os.remove(temp)

        return archive

    def extract_archive_from_base64(self, data, filename):
        """Extract archive and put file in a list of dictionaries."""

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.extract_archive(data, filename)

    def extract_archive(self, data, filename):
        """Extract archive and put file in a list of dictionaries."""
        return []
