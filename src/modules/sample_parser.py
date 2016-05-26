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

import glob
import hashlib
import logging
import os
import patoolib
import shutil
import ssdeep
import tempfile

log = logging.getLogger(__name__)


class Base64Error(ValueError):
    pass


class TempIOError(Exception):
    pass


class SampleParser(object):

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

        result = {
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

        # Check if it's a archive
        if not is_archive:
            if os.path.exists(file_):
                os.remove(file_)
            return result

        else:
            result['files'] = list()
            temp_dir = tempfile.mkdtemp()
            patoolib.extract_archive(file_, outdir=temp_dir, verbosity=-1)

            for i in glob.iglob(os.path.join(temp_dir, '*')):
                with open(i, 'rb') as f:
                    i_data = f.read()
                    i_filename = os.path.basename(i)
                    i_size = os.path.getsize(i)
                    md5, sha1, sha256, sha512, ssdeep_ = self.fingerprints(
                        i_data
                    )

                    result['files'].append(
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

            if os.path.exists(file_):
                os.remove(file_)

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

            return result
