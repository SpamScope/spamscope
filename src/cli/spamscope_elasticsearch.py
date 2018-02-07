#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

import argparse
import logging
import os
import runpy
import sys
import time
import warnings

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError

from elasticsearch_queries import query_sample


current = os.path.realpath(os.path.dirname(__file__))
__version__ = runpy.run_path(
    os.path.join(current, "..", "options.py"))["__version__"]


# Logger
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s] [%(levelname)s] [%(funcName)s] %(message)s")
ch.setFormatter(formatter)
log.addHandler(ch)


warnings.filterwarnings("ignore")


def get_args():
    parser = argparse.ArgumentParser(
        description="Tool to manage Elasticsearch for SpamScope",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(help="sub-commands", dest="subparser")
    connection = parser.add_mutually_exclusive_group()

    # Common args
    connection.add_argument(
        "-c",
        "--client-host",
        default=None,
        help="Elasticsearch client host",
        dest="client_host")

    # Common args
    connection.add_argument(
        "-u",
        "--url",
        default=None,
        help="RFC-1738 formatted URLs: https://user:secret@other_host:443/prd",
        dest="url")

    # Common args
    parser.add_argument(
        "-m",
        "--max-retry",
        default=10,
        type=int,
        help="Max retry for action",
        dest="max_retry")

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s {}'.format(__version__))

    # Replicas args
    replicas = subparsers.add_parser(
        "replicas", help="Update the number of replicas")

    replicas.add_argument(
        "-n",
        "--nr-replicas",
        default=0,
        type=int,
        help="Number of replicas.",
        dest="nr_replicas")

    replicas.add_argument(
        "-i",
        "--index",
        default="_all",
        help=("A comma-separated list of index names; use _all "
              "or empty string to perform the operation on all indices."),
        dest="index")

    # Template args
    template = subparsers.add_parser(
        "template", help="Update/add template")

    template.add_argument(
        "-p",
        "--template-path",
        required=True,
        help="Path of template.",
        dest="template_path")

    template.add_argument(
        "-n",
        "--template-name",
        required=True,
        help="Template name",
        dest="template_name")

    # Get payload args
    get_payload = subparsers.add_parser(
        "get-payload", help="Get sample payload from Elasticsearch")

    get_payload.add_argument(
        "-i",
        "--index",
        default="_all",
        help=("A comma-separated list of index names; use _all "
              "or empty string to perform the operation on all indices."),
        dest="index")

    get_payload.add_argument(
        "-a",
        "--hash-value",
        required=True,
        help="Sample hash to get",
        dest="hash_value")

    get_payload.add_argument(
        "-f",
        "--file-output",
        required=True,
        help="File output",
        dest="file_output")

    return parser.parse_args()


def get_payload(es, index, hash_value, file_output):
    len_hashes = dict(
        [(32, "md5"), (40, "sha1"), (64, "sha256"),
         (128, "sha512")])
    try:
        hash_key = len_hashes[len(hash_value)]
    except KeyError:
        raise KeyError("invalid hash {!r}".format(hash_value))
    else:
        body = query_sample % {"hash_key": hash_key, "hash_value": hash_value}

        r = es.search(
            index=index,
            body=body,
            size=1)["hits"]["hits"][0]["_source"]

        log.info("Filename: {!r}, Content-Type: {!r}, sha256: {!r}".format(
            r["filename"], r["Content-Type"], r["sha256"]))

        try:
            content_transfer_encoding = r["content_transfer_encoding"]
        except KeyError:
            # All archived files have base64 payload
            content_transfer_encoding = "base64"

        payload = r["payload"]
        write_type = "w"

        if content_transfer_encoding == "base64":
            payload = payload.decode("base64")
            write_type = "wb"

        with open(file_output, write_type) as f:
            f.write(payload)

        log.info("Sample file {!r} saved on {!r}".format(
            hash_value, file_output))


def update_nr_replicas(es, max_retry, nr_replicas, index):
    for i in range(max_retry, 0, -1):
        try:
            es.indices.put_settings(
                body={"index": {"number_of_replicas": int(nr_replicas)}},
                index=index,
                allow_no_indices=True)
            log.info("Updating replicas done")
            return

        except (ConnectionError, NotFoundError):
            log.warning(
                "Updating replicas failed. Waiting for {} sec".format(i))
            time.sleep(i)

    log.error("Updating replicas definitely failed")


def update_template(es, max_retry, template_path, template_name):
    with open(template_path) as f:
        body = f.read()

    for i in range(max_retry, 0, -1):
        try:
            es.indices.put_template(name=template_name, body=body)
            log.info("Updating template {!r} done".format(template_name))
            return

        except (ConnectionError, NotFoundError):
            log.warning(
                "Updating template {!r} failed. Waiting for {} sec".format(
                    template_name, i))
            time.sleep(i)

    log.error("Updating template {!r} definitely failed".format(template_name))


def main():
    # Command line args
    args = get_args()

    if args.client_host:
        es = Elasticsearch(args.client_host)
    elif args.url:
        es = Elasticsearch(args.url, verify_certs=False)

    # replicas
    if args.subparser == "replicas":
        update_nr_replicas(
            es=es,
            max_retry=args.max_retry,
            nr_replicas=args.nr_replicas,
            index=args.index)

    # template
    elif args.subparser == "template":
        update_template(
            es=es,
            max_retry=args.max_retry,
            template_path=args.template_path,
            template_name=args.template_name)

    # get_payload
    elif args.subparser == "get-payload":
        get_payload(
            es=es,
            index=args.index,
            hash_value=args.hash_value,
            file_output=args.file_output)


if __name__ == "__main__":
    main()
