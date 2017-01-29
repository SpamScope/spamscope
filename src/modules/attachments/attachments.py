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

from __future__ import absolute_import, print_function, unicode_literals

try:
    from UserList import UserList
except ImportError:
    from collections import UserList

import copy
import os
import patoolib
import shutil
import six
import tempfile
from .utils import fingerprints, check_archive, contenttype, extension


class HashError(IndexError):
    pass


class Attachments(UserList):

    def __getattr__(self, name):
        try:
            return self._kwargs[name]
        except KeyError:
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    def __call__(self):
        self.run()

    def _intelligence(self):
        pass

    def removeall(self):
        """Remove all items from object. """
        del self[:]

    def run(self):
        """Run processing on items in memory. """
        self._addmetadata()

    def reload(self, **kwargs):
        """Reload all configuration parameters"""
        self._kwargs = kwargs

    def filenamestext(self):
        """Return a string with the filenames of all attachments. """
        filenames = six.text_type()

        for i in self:
            try:
                filenames += i["filename"] + "\n"

                for j in i.get("files", []):
                    filenames += j["filename"] + "\n"

            except UnicodeDecodeError:
                continue

        return filenames.strip()

    def payloadstext(self):
        """Return a string with the not binary payloads of all attachments. """
        text = six.text_type()

        for i in self:
            try:
                if i.get("is_filtered"):
                    continue

                if not i.get("is_archive"):
                    text += i["payload"].decode("base64") + "\n"
                    continue

                for j in i.get("files", []):
                    text += j["payload"].decode("base64") + "\n"

            except UnicodeDecodeError:
                # This exception happens with binary payloads
                continue

        return text.strip()

    def pophash(self, attach_hash):
        """Remove the item with attach_hash from object. """
        len_hashes = dict([(32, "md5"), (40, "sha1"),
                          (64, "sha256"), (128, "sha512")])

        for n, i in enumerate(self):
            try:
                key = len_hashes[len(attach_hash)]
            except KeyError:
                raise HashError("invalid hash {!r}".format(attach_hash))

            if key in i and i[key] == attach_hash:
                self.pop(n)

    def filter(self, check_list, hash_type="sha1"):
        """Remove from memory the payloads with hash in check_list. """
        check_list = set(check_list)
        matches = set()

        for i in self:
            if i[hash_type] in check_list:
                i.pop("payload", None)
                i["is_filtered"] = True
                matches.add(i[hash_type])
                continue
            i["is_filtered"] = False

        return matches

    @staticmethod
    def _metadata(raw_dict):
        """ Return payload, file size and extension of raw data. """
        if raw_dict["content_transfer_encoding"] == "base64":
            payload = raw_dict["payload"].decode("base64")
        else:
            payload = raw_dict["payload"]

        size = len(payload)
        ext = extension(raw_dict["filename"])
        return (payload, size, ext)

    def _addmetadata(self):
        """For each item in memory add extra informations as: file extension,
        file size, content type, if is a archive and archived files.
        """
        for i in self:
            if not i.get("is_filtered", False):
                payload, size, ext = Attachments._metadata(i)
                content_type = contenttype(payload)
                flag, f = check_archive(payload, write_sample=True)

                i.update({
                    "extension": ext,
                    "size": size,
                    "Content-Type": content_type,
                    "is_archive": flag})

                if flag:
                    i["files"] = []
                    temp_dir = tempfile.mkdtemp()
                    patoolib.extract_archive(f, outdir=temp_dir, verbosity=-1)

                    for path, subdirs, files in os.walk(temp_dir):
                        for name in files:
                            j = os.path.join(path, name)

                            with open(j, "rb") as a:
                                t = {}
                                payload = a.read()
                                content_type = contenttype(payload)
                                filename = os.path.basename(j)

                                t["filename"] = filename
                                t["extension"] = extension(filename)
                                t["size"] = len(payload)
                                t["Content-Type"] = content_type
                                t["payload"] = payload.encode("base64")
                                t["md5"], t["sha1"], t["sha256"], \
                                    t["sha512"], t["ssdeep"] = fingerprints(
                                        payload)

                                i["files"].append(t)

                    # Remove temp dir for archived files
                    if os.path.exists(temp_dir):
                        shutil.rmtree(temp_dir)

                # Remove temp file from filesystem
                if os.path.exists(f):
                    os.remove(f)

    @classmethod
    def withhashes(cls, attachments=[]):
        """Alternative costructor that add hashes to the items. """
        r = copy.deepcopy(attachments)

        for i in r:
            if i.get("content_transfer_encoding") == "base64":
                payload = i["payload"].decode("base64")
            else:
                payload = i["payload"]

            i["md5"], i["sha1"], i["sha256"], i["sha512"], i["ssdeep"] = \
                fingerprints(payload)

        return cls(r)
