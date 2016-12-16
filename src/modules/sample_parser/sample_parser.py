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
import magic
import os
import patoolib
import shutil
import ssdeep
import tempfile
from .exceptions import Base64Error, TempIOError
from .virustotal_processing import VirusTotalProcessing
from .tika_processing import TikaProcessing
from .thug_processing import ThugProcessing

log = logging.getLogger(__name__)


class SampleParser(object):
    """ This class processes a raw mail attachment to add
    all processing output (TikaProcessing, VirusTotalPublicApi ThugProcessing).

    Args:
        blacklist_content_types (set): content types that will not process.
                                       Default: set()
        thug_enabled (boolean): enable Thug analysis is True. Default: False
        tika_enabled (boolean): enable Apache Tika analysis is True.
                                Default: False
        virustotal_enabled (boolean): enable VirusTotal analysis is True.
                                      Default: False
        tika_jar (string): Apache Tika App jar path
        tika_memory_allocation (string): Memory to give to Apache Tika App
        tika_valid_content_types (set): Content types to analyze with
                                        Apache Tika
        virustotal_api_key (string): VirusTotal API key
        thug_referer (string): Referer to use for analysis
        thug_extensions (list or set): list of extensions to analyze
        thug_user_agents (list or set): list of user agents to use for analysis
    """

    def __init__(self, **kwargs):
        self._kwargs = kwargs

    def __getattr__(self, name):
        try:
            return self._kwargs[name]
        except KeyError:
            # Default values
            if name in ("tika_enabled", "virustotal_enabled", "thug_enabled"):
                return False
            elif name in ("blacklist_content_types"):
                return set()
            else:
                msg = "'{0}' object has no attribute '{1}'"
                raise AttributeError(msg.format(type(self).__name__, name))

    @property
    def result(self):
        return self._result

    @staticmethod
    def fingerprints_from_base64(data):
        """This function return the fingerprints of data from base64.

        Args:
            data (string): raw data in base64

        Returns:
            tuple: fingerprints md5, sha1, sha256, sha512, ssdeep
        """

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return SampleParser.fingerprints(data)

    @staticmethod
    def fingerprints(data):
        """This function return the fingerprints of data.

        Args:
            data (string): raw data

        Returns:
            tuple: fingerprints md5, sha1, sha256, sha512, ssdeep
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

    @staticmethod
    def is_archive_from_base64(data, write_sample=False):
        """Check if data is an archive.

        Args:
            data (string): raw data in base64
            write_sample (boolean): if True it writes sample on disk

        Returns:
            boolean: only True is archive (False otherwise)
                     if write_sample is False
            tuple (boolean, string): True is archive (False otherwise) and
                                     sample path
        """

        try:
            data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return SampleParser.is_archive(data, write_sample)

    @staticmethod
    def is_archive(data, write_sample=False):
        """Check if data is an archive.

        Args:
            data (string): raw data
            write_sample (boolean): if True it writes sample on disk

        Returns:
            boolean: only True is archive (False otherwise)
                     if write_sample is False
            tuple (boolean, string): True is archive (False otherwise) and
                                     sample path
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

    @staticmethod
    def make_attachment(data, filename, mail_content_type, transfer_encoding):
        """ This method creates dict result with basic informations.

        Args:
            data (string): raw data
            filename (string): name of attachment file
            mail_content_type (string): content type in email header
            transfer_encoding (string): transfer encoding in email header

        Returns:
            Dict with attachment details (filename, payload, etc.)
        """

        is_archive, file_ = SampleParser.is_archive(data, write_sample=True)
        size = os.path.getsize(file_)
        extension = os.path.splitext(filename)

        attachment = {
            'filename': filename,
            'extension': extension[-1].lower() if len(extension) > 1 else None,
            'payload': data.encode('base64'),
            'mail_content_type': mail_content_type,
            'content_transfer_encoding': transfer_encoding,
            'size': size,
            'is_archive': is_archive}

        if is_archive:
            attachment['files'] = list()
            temp_dir = tempfile.mkdtemp()
            patoolib.extract_archive(file_, outdir=temp_dir, verbosity=-1)

            for path, subdirs, files in os.walk(temp_dir):
                for name in files:
                    i = os.path.join(path, name)

                    with open(i, 'rb') as f:
                        i_data = f.read()
                        i_filename = os.path.basename(i)
                        i_extension = os.path.splitext(i_filename)
                        i_size = os.path.getsize(i)

                        attachment['files'].append({
                            'filename': i_filename,
                            'extension': i_extension[-1].lower() if len(
                                i_extension) > 1 else None,
                            'payload': i_data.encode('base64'),
                            'size': i_size})

            # Remove temp dir for archived files
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

        # Remove temp file system sample
        if os.path.exists(file_):
            os.remove(file_)

        return attachment

    @staticmethod
    def add_fingerprints(attachment):
        """This method adds fingerprints to attachment.

        Args:
            attachment (dict): dict with details of mail attachment

        Returns:
            Add fingerprints to attachment argument
        """

        md5, sha1, sha256, sha512, ssdeep_ = SampleParser.fingerprints(
            attachment['payload'].decode('base64'))

        attachment['md5'] = md5
        attachment['sha1'] = sha1
        attachment['sha256'] = sha256
        attachment['sha512'] = sha512
        attachment['ssdeep'] = ssdeep_

        if attachment['is_archive']:
            for i in attachment['files']:
                md5, sha1, sha256, sha512, ssdeep_ = SampleParser.fingerprints(
                    i['payload'].decode('base64'))

                i['md5'] = md5
                i['sha1'] = sha1
                i['sha256'] = sha256
                i['sha512'] = sha512
                i['ssdeep'] = ssdeep_

    @staticmethod
    def add_content_type(attachment):
        """This method adds content type to result attribute """

        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(
            attachment['payload'].decode('base64'))

        attachment['Content-Type'] = content_type

        if attachment['is_archive']:
            for i in attachment['files']:
                content_type = mime.from_buffer(
                    i['payload'].decode('base64'))

                # To manage blacklist content types add Content-Type to the
                # files in archive
                i['Content-Type'] = content_type

    def _filter_content_type(self, attachment):
        """This method removes from attachment the samples with
        content type in blacklist.

        Args:
            attachment (dict): dict with details of mail attachment

        Returns:
            The results are given in attachment argument
        """

        if self.blacklist_content_types:
            content_type = attachment['Content-Type']
            if content_type in self.blacklist_content_types:
                attachment = None
                return

            if attachment['is_archive']:
                attachment['files'] = [
                    i
                    for i in attachment['files']
                    if i['Content-Type'] not in self.blacklist_content_types]

    def parse_sample(self, data, filename, mail_content_type=None,
                     transfer_encoding=None):
        """This method analyzes sample and add metadata.

        Args:
            data (string): raw data
            filename (string): name of attachment file
            mail_content_type (string): content type in email header
            transfer_encoding (string): transfer encoding in email header

        Returns:
            The results are given in result attribute
        """

        # Basic informations without fingerprints
        self._result = SampleParser.make_attachment(
            data, filename, mail_content_type, transfer_encoding)

        # Add content type
        SampleParser.add_content_type(self.result)

        # Filter content type
        # If content type in blacklist_content_types result = None
        self._filter_content_type(self.result)

        if self.result:

            # Add fingerprints
            SampleParser.add_fingerprints(self.result)

            # Add Tika analysis
            if self.tika_enabled:
                TikaProcessing(
                    jar=self.tika_jar,
                    valid_content_types=self.tika_valid_content_types,
                    memory_allocation=self.tika_memory_allocation
                ).process(self.result)

            # Add VirusTotal analysis
            if self.virustotal_enabled:
                VirusTotalProcessing(
                    api_key=self.virustotal_api_key).process(self.result)

            if self.thug_enabled:
                ThugProcessing(
                    referer=self.thug_referer,
                    extensions=self.thug_extensions,
                    user_agents=self.thug_user_agents,
                ).process(self.result)

    def parse_sample_from_base64(self, data, filename, mail_content_type=None,
                                 transfer_encoding=None):
        """This method analyzes sample and add metadata.

        Args:
            data (string): raw data in base64
            filename (string): name of attachment file
            mail_content_type (string): content type in email header
            transfer_encoding (string): transfer encoding in email header

        Returns:
            The results are given in result attribute
        """

        try:
            if transfer_encoding == 'base64':
                data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.parse_sample(
            data, filename, mail_content_type, transfer_encoding)
