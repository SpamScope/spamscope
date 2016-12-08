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
import re
import shutil
import ssdeep
import tempfile
from abc import ABCMeta, abstractmethod
from tikapp import TikaApp
from virus_total_apis import PublicApi as VirusTotalPublicApi

log = logging.getLogger(__name__)


class Base64Error(ValueError):
    pass


class TempIOError(Exception):
    pass


class InvalidAttachment(ValueError):
    pass


class VirusTotalApiKeyInvalid(ValueError):
    pass


class InvalidContentTypes(ValueError):
    pass


class MissingArgument(ValueError):
    pass


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


class TikaProcessing(AbstractProcessing):
    """ This class processes the output mail attachments to add
    Apache Tika analysis.

    Keyword arguments:
    jar -- path of Apache Tika App jar
    valid_content_types -- list of contents types to analyze
    memory_allocation -- memory to give to Apache Tika App
    """

    def __init__(self, **kwargs):
        super(TikaProcessing, self).__init__(**kwargs)

        # Init Tika
        self._tika_client = TikaApp(
            file_jar=self.jar,
            memory_allocation=self.memory_allocation)

    def __setattr__(self, name, value):
        super(TikaProcessing, self).__setattr__(name, value)

        if name == "valid_content_types":
            if not isinstance(value, set) and not isinstance(value, list):
                raise InvalidContentTypes("Content types must be set or list")

            self._kwargs[name] = value

    def _check_arguments(self):
        """
        This method check if all mandatory arguments are given
        """

        if 'jar' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format('jar', type(self).__name__))

        if 'valid_content_types' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format(
                'valid_content_types', type(self).__name__))

        if 'memory_allocation' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format(
                'memory_allocation', type(self).__name__))

    def process(self, attachments):
        """
        This method updates the attachments results with the Tika output
        """
        super(TikaProcessing, self).process(attachments)

        if attachments['Content-Type'] in self.valid_content_types:
            attachments['tika'] = self._tika_client.extract_all_content(
                payload=attachments['payload'],
                convert_to_obj=True)


class VirusTotalProcessing(AbstractProcessing):
    """ This class processes the output mail attachments to add
    VirusTotal report.

    Keyword arguments:
    api_key -- VirusTotal api key
    """

    def _check_arguments(self):
        """
        This method check if all mandatory arguments are given
        """

        if 'api_key' not in self._kwargs:
            msg = "Argument '{0}' not in object '{1}'"
            raise MissingArgument(msg.format('api_key', type(self).__name__))

    def process(self, attachments):
        """
        This method updates the attachments results with the Virustotal report
        """
        super(VirusTotalProcessing, self).process(attachments)

        if not self.api_key or not re.match(r'[a-z0-9]{64}', self.api_key):
            raise VirusTotalApiKeyInvalid("Add a valid VirusTotal API key!")

        vt = VirusTotalPublicApi(self.api_key)

        sha1 = attachments['sha1']
        result = vt.get_file_report(sha1)
        if result:
            attachments['virustotal'] = result

        if attachments['is_archive']:
            for i in attachments['files']:
                i_sha1 = i['sha1']
                i_result = vt.get_file_report(i_sha1)
                if i_result:
                    i['virustotal'] = i_result


class ThugProcessing(AbstractProcessing):
    pass


class SampleParser(object):

    def __init__(
        self,
        blacklist_content_types=set(),
        virustotal_enabled=False,
        tika_enabled=False,
        virustotal_api_key=None,
        tika_jar=None,
        tika_memory_allocation=None,
        tika_valid_content_types=set()
    ):
        self._virustotal_enabled = virustotal_enabled
        self._tika_enabled = tika_enabled
        self._blacklist_content_types = blacklist_content_types
        self._virustotal_api_key = virustotal_api_key
        self._tika_jar = tika_jar
        self._tika_memory_allocation = tika_memory_allocation
        self._tika_valid_content_types = tika_valid_content_types

    @property
    def virustotal_enabled(self):
        return self._virustotal_enabled

    @property
    def tika_enabled(self):
        return self._tika_enabled

    @property
    def blacklist_content_types(self):
        return self._blacklist_content_types

    @property
    def virustotal_api_key(self):
        return self._virustotal_api_key

    @property
    def tika_jar(self):
        return self._tika_jar

    @property
    def tika_memory_allocation(self):
        return self._tika_memory_allocation

    @property
    def tika_valid_content_types(self):
        return self._tika_valid_content_types

    @property
    def result(self):
        return self._result

    @staticmethod
    def fingerprints_from_base64(data):
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

        return SampleParser.fingerprints(data)

    @staticmethod
    def fingerprints(data):
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

    @staticmethod
    def is_archive_from_base64(data, write_sample=False):
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

        return SampleParser.is_archive(data, write_sample)

    @staticmethod
    def is_archive(data, write_sample=False):
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

    def _create_sample_result(
        self,
        data,
        filename,
        mail_content_type,
        transfer_encoding,
    ):
        """ Create dict result with basic informations."""

        is_archive, file_ = self.is_archive(data, write_sample=True)
        size = os.path.getsize(file_)
        extension = os.path.splitext(filename)

        self._result = {
            'filename': filename,
            'extension': extension[-1].lower() if len(extension) > 1 else None,
            'payload': data.encode('base64'),
            'mail_content_type': mail_content_type,
            'content_transfer_encoding': transfer_encoding,
            'size': size,
            'is_archive': is_archive}

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
                        i_extension = os.path.splitext(i_filename)
                        i_size = os.path.getsize(i)

                        self._result['files'].append({
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

    def _add_fingerprints(self):
        """ Add fingerprints."""

        md5, sha1, sha256, sha512, ssdeep_ = self.fingerprints(
            self._result['payload'].decode('base64'))

        self._result['md5'] = md5
        self._result['sha1'] = sha1
        self._result['sha256'] = sha256
        self._result['sha512'] = sha512
        self._result['ssdeep'] = ssdeep_

        if self._result['is_archive']:
            for i in self._result['files']:
                md5, sha1, sha256, sha512, ssdeep_ = self.fingerprints(
                    i['payload'].decode('base64'))

                i['md5'] = md5
                i['sha1'] = sha1
                i['sha256'] = sha256
                i['sha512'] = sha512
                i['ssdeep'] = ssdeep_

    def _add_content_type(self):
        mime = magic.Magic(mime=True)
        content_type = mime.from_buffer(
            self._result['payload'].decode('base64'))

        self._result['Content-Type'] = content_type

        if self._result['is_archive']:
            for i in self._result['files']:
                content_type = mime.from_buffer(
                    i['payload'].decode('base64'))

                # To manage blacklist content types add Content-Type to the
                # files in archive
                i['Content-Type'] = content_type

    def _remove_content_type(self):
        """Remove from results the samples with content type in blacklist."""

        if self.blacklist_content_types:
            content_type = self._result['Content-Type']
            if content_type in self.blacklist_content_types:
                self._result = None
                return

            if self._result['is_archive']:
                self._result['files'] = [
                    i
                    for i in self._result['files']
                    if i['Content-Type'] not in self.blacklist_content_types]

    def parse_sample(
        self,
        data,
        filename,
        mail_content_type=None,
        transfer_encoding=None,
    ):
        """Analyze sample and add metadata.
        If it's an archive, extract it and put files in a list of dictionaries.
        """

        # Basic informations without fingerprints
        self._create_sample_result(
            data,
            filename,
            mail_content_type,
            transfer_encoding,
        )

        # Add content type
        self._add_content_type()

        # Blacklist content type
        # If content type in blacklist_content_types result = None
        self._remove_content_type()

        if self.result:

            # Add fingerprints
            self._add_fingerprints()

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

    def parse_sample_from_base64(
        self,
        data,
        filename,
        mail_content_type=None,
        transfer_encoding=None,
    ):
        """Analyze sample and add metadata.
        If it's a archive, extract it and put files in a list of dictionaries.
        Data is in base64.
        """

        try:
            if transfer_encoding == 'base64':
                data = data.decode('base64')
        except:
            raise Base64Error("Data '{}' is NOT correct".format(data))

        return self.parse_sample(
            data,
            filename,
            mail_content_type,
            transfer_encoding)
