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
import shutil
import ssdeep
import tempfile
import tika
from tika import parser as tika_parser

log = logging.getLogger(__name__)


class Base64Error(ValueError):
    pass


class TempIOError(Exception):
    pass


class SampleParser(object):

    def __init__(
        self,
        tika_enabled=False,
        tika_server_endpoint="http://localhost:9998"
    ):
        """ Initialize sample parser.
        To enable tika parsing: tika_enabled=True.
        Default server point to localhost port 9998.
        Use tika_server_endpoint to change it.
        """

        self._tika_enabled = tika_enabled
        self._tika_server_endpoint = tika_server_endpoint

        if tika_enabled:
            tika.TikaClientOnly = True
            tika.TIKA_SERVER_ENDPOINT = tika_server_endpoint

    @property
    def tika_enabled(self):
        return self._tika_enabled

    @property
    def tika_server_endpoint(self):
        return self._tika_server_endpoint

    def fingerprints_from_base64(self, data):
        """This function return the fingerprints of data from base64:
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

    def is_archive_from_base64(self, data, write_sample=False):
        """If write_sample=False this function return only a boolean:
            True if data is a archive, else False.
        Else write_sample=True this function return a tuple:
            (is_archive, path_sample)
        Data is in base64.
        """

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.is_archive(data, write_sample)

    def is_archive(self, data, write_sample=False):
        """If write_sample=False this function return only a boolean:
            True if data is a archive, else False.
        Else write_sample=True this function return a tuple:
            (is_archive, path_sample)
        """

        is_archive = True
        try:
            temp = tempfile.mkstemp()[1]
            with open(temp, 'wb') as f:
                f.write(data)
        except:
            raise TempIOError("Failed opening '{}' file".format(temp))

        try:
            patoolib.test_archive(temp, verbosity=-1)
        except:
            is_archive = False
        finally:
            if write_sample:
                return is_archive, temp
            else:
                os.remove(temp)
                return is_archive

    def parse_sample_from_base64(self, data, filename):
        """Analyze sample and add metadata.
        If it's a archive, extract it and put files in a list of dictionaries.
        Data is in base64.
        """

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.parse_sample(data, filename)

    def parse_sample(self, data, filename):
        """Analyze sample and add metadata.
        If it's an archive, extract it and put files in a list of dictionaries.
        """

        # Sample
        is_archive, file_ = self.is_archive(data, write_sample=True)
        size = os.path.getsize(file_)
        md5, sha1, sha256, sha512, ssdeep_ = self.fingerprints(data)

        self._result = {
            'filename': filename,
            'payload': data.encode('base64'),
            'size': size,
            'md5': md5,
            'sha1': sha1,
            'sha256': sha256,
            'sha512': sha512,
            'ssdeep': ssdeep_,
            'is_archive': is_archive,
        }

        if is_archive:
            self._result['files'] = list()
            temp_dir = tempfile.mkdtemp()
            patoolib.extract_archive(file_, outdir=temp_dir, verbosity=-1)

            for path, subdirs, files in os.walk(temp_dir):
                for name in files:
                    i = os.path.join(path, name)

                    with open(i, 'rb') as f:
                        i_data = f.read()
                        i_filename = os.path.basename(i)
                        i_size = os.path.getsize(i)
                        md5, sha1, sha256, sha512, ssdeep_ = self.fingerprints(
                            i_data
                        )

                        self._result['files'].append(
                            {
                                'filename': i_filename,
                                'payload': i_data.encode('base64'),
                                'size': i_size,
                                'md5': md5,
                                'sha1': sha1,
                                'sha256': sha256,
                                'sha512': sha512,
                                'ssdeep': ssdeep_,
                            }
                        )
            # Remove temp dir for archived files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        # Remove temp file system sample
        if os.path.exists(file_):
            os.remove(file_)

        # Add tika output
        if self.tika_enabled:
            self.add_tika_output()

    def add_tika_output(self):
        payload = self._result['payload'].decode('base64')
        self._result['tika'] = tika_parser.from_buffer(payload)

        if self._result['is_archive']:
            for i in self._result['files']:
                i_payload = i['payload'].decode('base64')
                i['tika'] = tika_parser.from_buffer(i_payload)

    @property
    def result(self):
        return self._result
