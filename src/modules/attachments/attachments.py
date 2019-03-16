#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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

import base64
import copy
import datetime
import logging
import os
import shutil
import tempfile
from operator import itemgetter

import patoolib
from patoolib.util import PatoolError
import six

from .exceptions import HashError, ContentTypeError
from .post_processing import processors
from .utils import fingerprints, check_archive, contenttype, extension


log = logging.getLogger(__name__)

p_ordered = [i[0] for i in sorted(processors, key=itemgetter(1))]


class Attachments(UserList):
    _kwargs = {}

    def __getattr__(self, name):
        try:
            return self._kwargs[name]
        except KeyError:
            if name in ("commons"):
                return {}
            msg = "'{0}' object has no attribute '{1}'"
            raise AttributeError(msg.format(type(self).__name__, name))

    def __call__(self, intelligence=True):
        self.run(intelligence)

    def _intelligence(self):
        """
        Post processing attachments with third party tools
        """
        for p in p_ordered:
            try:
                p(getattr(self, p.__name__), self)
            except AttributeError:
                log.warning(
                    "AttributeError: {!r} doesn't exist".format(p.__name__))

    def removeall(self):
        """Remove all items from object. """
        del self[:]

    def run(self, intelligence=True):
        """Run processing on items in memory. """

        self._addmetadata()

        self._filtercontenttypes()

        self._filterforsize()

        if intelligence:
            self._intelligence()

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
        else:
            return filenames.strip()

    def payloadstext(self):
        """Return a string with the not binary payloads of all attachments. """
        text = six.text_type()

        for i in self:
            try:
                if i.get("is_filtered"):
                    continue

                if not i.get("is_archive"):
                    if i["content_transfer_encoding"] == "base64":
                        text += base64.b64decode(i["payload"]) + "\n"
                    else:
                        text += i["payload"] + "\n"
                    continue

                for j in i.get("files", []):
                    text += base64.b64decode(j["payload"]) + "\n"

            except UnicodeDecodeError:
                # This exception happens with binary payloads
                continue
        else:
            return text.strip()

    def popcontenttype(self, content_type):
        """ Given a content type remove attachments with same content type,
        also in files in archive.
        """
        content_type = content_type.lower()
        remove = []

        for i in self:
            filtered = i.get("is_filtered", False)
            m_content_type = i["mail_content_type"].lower()

            if not filtered:
                try:
                    if i["Content-Type"].lower() == content_type:
                        remove.append(i)
                        continue

                    inner_remove = []
                    for j in i.get("files", []):
                        if j["Content-Type"].lower() == content_type:
                            inner_remove.append(j)
                except KeyError:
                    raise ContentTypeError("Content-Type key missing. "
                                           "Add metadata with method '.run()'")
                else:
                    # Remove inner
                    for j in inner_remove:
                        i["files"].remove(j)

            # Patch
            # If attach is filtered and content_type in whitelist
            # you should remove sample from results.
            # You can't use Content-Type because we don't have payload, so
            # we use mail_content_type
            elif (filtered and m_content_type == content_type):
                remove.append(i)

        else:
            # Remove
            for i in remove:
                self.remove(i)

    def pophash(self, attach_hash):
        """Remove the item with attach_hash from object. """
        len_hashes = dict([(32, "md5"), (40, "sha1"),
                          (64, "sha256"), (128, "sha512")])
        to_remove = []

        for i in self:
            try:
                key = len_hashes[len(attach_hash)]
            except KeyError:
                raise HashError("invalid hash {!r}".format(attach_hash))
            else:
                if key in i and i[key] == attach_hash:
                    to_remove.append(i)
        else:
            for i in to_remove:
                self.remove(i)

    def _filterforsize(self):
        """
        Filter all attachments or archived files greater than fixed size
        """
        if not self.commons.get("size.filter.enabled", False):
            return

        max_size = int(self.commons.get("max.size", 3145728))

        for i in self:
            if not i.get("is_filtered", False):
                if i["size"] >= max_size:
                    i.pop("payload", None)
                    i.pop("files", None)
                    i["is_filtered"] = True
                    i["filter_reason"] = "greater that {} bytes".format(
                        max_size)
                else:
                    if i.get("files", []):
                        files = []
                        for j in i["files"]:
                            if j["size"] < max_size:
                                files.append(j)
                            else:
                                log.warning(
                                    "File {!r} greater than {} bytes".format(
                                        j["sha1"], max_size))

                        if len(files) != len(i["files"]):
                            i["filter_files"] = True
                            if files:
                                i["files"] = files
                            else:
                                i.pop("files", None)

    def _filtercontenttypes(self):
        """Filtering of all content types in
        'filter_cont_types' parameter.
        """
        for i in self.commons.get("blacklist_content_types", set()):
            self.popcontenttype(i)

    def filter(self, check_list, hash_type="sha1"):
        """Remove from memory the payloads with hash in check_list. """
        check_list = set(check_list)
        analyzed = set()

        for i in self:
            analyzed.add(i[hash_type])

            if i[hash_type] in check_list:
                i.pop("payload", None)
                i["is_filtered"] = True
                continue

            i["is_filtered"] = False

        else:
            return analyzed

    @staticmethod
    def _metadata(raw_dict):
        """ Return payload, file size and extension of raw data. """
        if raw_dict["binary"]:
            try:
                payload = base64.b64decode(raw_dict["payload"])
            except TypeError, e:
                # https://gist.github.com/perrygeo/ee7c65bb1541ff6ac770
                raw_dict["payload"] += "==="
                log.warning(
                    "Added '===' to payload base64 for sample {!r}".format(
                        raw_dict["md5"]))
                payload = base64.b64decode(raw_dict["payload"])
                raw_dict.setdefault("errors", []).append(repr(e))
        else:
            payload = raw_dict["payload"]

        size = len(payload)
        ext = extension(raw_dict["filename"])
        return (payload, size, ext)

    def _addmetadata(self):
        """For each item in memory add extra informations as: file extension,
        file size, content type, if is a archive and archived files.
        """
        bl_list = self.commons.get("not_extract_content_types", set())

        for i in self:
            i["analisys_date"] = datetime.datetime.utcnow().isoformat()

            if not i.get("is_filtered", False):
                payload, size, ext = Attachments._metadata(i)
                content_type = contenttype(payload)
                flag, f = check_archive(payload, write_sample=True)

                i.update({
                    "extension": ext,
                    "size": size,
                    "Content-Type": content_type,
                    "is_archive": flag})

                if flag and content_type not in bl_list:
                    i["files"] = []
                    temp_dir = tempfile.mkdtemp()

                    try:
                        patoolib.extract_archive(
                            f, outdir=temp_dir, verbosity=-1)

                    except PatoolError as e:
                        log.warning(
                            "PatoolError archive md5 {!r}. Details: {}".format(
                                i["md5"], repr(e)))

                    else:
                        for path, subdirs, files in os.walk(temp_dir):
                            for name in files:
                                j = os.path.join(path, name)

                                with open(j, "rb") as a:
                                    t = {}
                                    payload = a.read()
                                    content_type = contenttype(payload)
                                    filename = os.path.basename(j)

                                    t["analisys_date"] = \
                                        datetime.datetime.utcnow().isoformat()
                                    t["filename"] = filename
                                    t["extension"] = extension(filename)
                                    t["size"] = len(payload)
                                    t["Content-Type"] = content_type
                                    t["payload"] = payload.encode("base64")
                                    t["is_filtered"] = False
                                    t["md5"], t["sha1"], t["sha256"], \
                                        t["sha512"], t["ssdeep"] = \
                                        fingerprints(payload)
                                    i["files"].append(t)
                    finally:
                        try:
                            # Remove temp dir for archived files
                            shutil.rmtree(temp_dir)
                        except OSError:
                            pass

                try:
                    # Remove temp file from filesystem
                    os.remove(f)
                except OSError:
                    pass

    @classmethod
    def withhashes(cls, attachments=[]):
        """Alternative costructor that add hashes to the items. """
        r = copy.deepcopy(attachments)

        for i in r:
            if i.get("content_transfer_encoding") == "base64":
                try:
                    payload = base64.b64decode(i["payload"])
                except TypeError, e:
                    try:
                        # try to add === to decode base64
                        payload = base64.b64decode(i["payload"] + "===")
                    except TypeError:
                        # if fails maybe is text, with fake base64 header
                        payload = i["payload"]
                    finally:
                        i.setdefault("errors", []).append(
                            repr(e) + " Fake base64")
            else:
                payload = i["payload"]

            i["md5"], i["sha1"], i["sha256"], i["sha512"], i["ssdeep"] = \
                fingerprints(payload)
        else:
            return cls(r)
