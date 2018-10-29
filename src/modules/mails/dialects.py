#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2018 Fedele Mantuano (https://www.linkedin.com/in/fmantuano/)

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

"""
This module is based on Analysis of SMTP dialects
(https://sissden.eu/blog/analysis-of-smtp-dialects)
"""


import datetime
import logging
import re

from operator import itemgetter

try:
    from elasticsearch import Elasticsearch
    from elasticsearch import ElasticsearchException
except ImportError:
    raise ImportError("To use dialects module, you must use Elasticsearch")

try:
    from modules.attachments import fingerprints
except ImportError:
    from ...modules.attachments import fingerprints


log = logging.getLogger(__name__)


DIALECT_CLIENT_REGX_SORTED = [
    (re.compile(r'(?:ehlo|helo)\s*', re.I), 0),
    (re.compile(r'mail\s+from\s*:?\s*', re.I), 1),
    (re.compile(r'rcpt\s+to\s*:?\s*', re.I), 2),
    (re.compile(r'^[\b\s]*data[\b\s]*$', re.I), 3),
    (re.compile(r'^[\b\s]*quit[\b\s]*$', re.I), 4),
]


# This query gets the code in postfix index
query_code = """
{
  "query": {
    "term": {
      "message_id.keyword": {
        "value": "%(message_id)s"
      }
    }
  }
}
"""

# This query gets the client in postfix index
query_client = """
{
  "query": {
    "bool": {
      "filter": {
        "term": {
          "tags": "client"
        }
      },
      "must": [
        {
          "term": {
            "code.keyword": {
              "value": "%(code)s"
            }
          }
        }
      ]
    }
  }
}
"""

# This query gets all communication from client and server
query_dialect = """
{
  "query": {
    "bool": {
      "must": [
        {
          "range": {
            "@timestamp": {
              "gte": "%(timestamp)s||-30s",
              "lte": "%(timestamp)s||+10s"
            }
          }
        },
        {
          "term": {
            "client_ip.keyword": {
              "value": "%(client_ip)s"
            }
          }
        },
        {
          "term": {
            "client_name.keyword": {
              "value": "%(client_name)s"
            }
          }
        },
        {
          "term": {
            "tags": {
              "value": "dialect"
            }
          }
        }
      ]
    }
  },
  "sort": [
    {
      "@timestamp": {
        "order": "asc"
      }
    }
  ]
}
"""


def get_elastic_indices(index_prefix="postfix-"):
    """
    This function gets an Elastisearch index prefix
    and returns a string comma-separated of indices of
    yesterday and today.
    The indices must be prefix-YEAR.MONTH.DAY
    (postfix-2018.09.07)

    Keyword Arguments:
        index_prefix {str} -- prefix of Elasticsearch
                        indices (default: {"postfix-"})

    Returns:
        {str} -- list comma-separated of indices
    """

    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    days = [today, yesterday]
    indices = ",".join(["postfix-{}".format(
        i.strftime("%Y.%m.%d")) for i in days])
    return indices


def get_messages(message_id, elastic_server, index_prefix, max_size=100):
    """
    This function returns a list with all SMTP messages between
    client and server (dialect)

    Arguments:
        message_id {string} -- email message-id header
        elastic_server {list/string} -- Elasticsearch server
        index_prefix {string} -- prefix of Postfix index

    Keyword Arguments:
        max_size {int} -- Max size of messages to save (default: {100})

    Returns:
        list -- List tuples of SMTP messages. Every tuple has actor and message
    """

    try:
        # get indices to query
        indices = get_elastic_indices(index_prefix)

        # connect to Elasticsearch
        es = Elasticsearch(hosts=elastic_server)

        # From message_id get code of comunication from client and server
        r = es.search(
            index=indices,
            body=query_code % {"message_id": message_id},
            ignore_unavailable=True)

        code = r["hits"]["hits"][0]["_source"]["code"]
        timestamp = r["hits"]["hits"][0]["_source"]["@timestamp"]
        log.debug("The code of {!r} is {!r}".format(message_id, code))

        # From code get client (ip and name)
        r = es.search(
            index=indices,
            body=query_client % {"code": code},
            ignore_unavailable=True)
        client_ip = r["hits"]["hits"][0]["_source"]["client_ip"]
        client_name = r["hits"]["hits"][0]["_source"]["client_name"]

        # From client get dialects
        r = es.search(
            index=indices,
            body=query_dialect % {
                "timestamp": timestamp,
                "client_ip": client_ip,
                "client_name": client_name},
            size=max_size,
            ignore_unavailable=True)
        messages = [(i["_source"]["actor"],
                    i["_source"]["dialect"]) for i in r["hits"]["hits"]]

    except ElasticsearchException:
        log.exception(
            "Failed query Elasticsearch for dialect: {!r}".format(message_id))

    except IndexError:
        log.debug("message-id {!r} not found".format(message_id))

    else:
        return messages


def get_messages_str(messages):
    """
    From messeges list returns a string with all
    conversation between client and server

    Arguments:
        messages {list} -- list of messages from get_messages

    Returns:
        str -- string of conversation
    """

    messages_str = ""
    for i in messages:
        messages_str += "{}: {}\n".format(i[0], i[1])
    return messages_str.strip("\n\t ")


def get_dialect(messages):
    """
    This function gets only the client parts related
    the SMTP command

    Arguments:
        messages {list} -- list of messages from get_messages

    Returns:
        list -- List of commands of client
    """

    dialect = set()
    for j in DIALECT_CLIENT_REGX_SORTED:
        for i in messages:
            if i[0] == "client":
                r = j[0].findall(i[1])
                if r:
                    dialect.add((r[0], j[1]))
    else:
        dialect = sorted(dialect, key=itemgetter(1))
        return [i[0] for i in dialect]


def get_dialect_str(dialect):
    """
    From list of dialect returns a string

    Arguments:
        dialect {list} -- output of get_dialect

    Returns:
        str -- string of client commands
    """

    return " ".join(dialect)


def get_dialect_fingerprints(dialect):
    """
    Given a dialect list returns the hashes of its string
    version

    Arguments:
        dialect {list} -- output of get_dialect

    Returns:
        namedtuple -- fingerprints md5, sha1, sha256, sha512, ssdeep
    """

    dialect_str = get_dialect_str(dialect)
    return fingerprints(dialect_str)


def make_dialect_report(
    message_id,
    elastic_server,
    index_prefix,
    max_size=100
):
    messages = get_messages(message_id, elastic_server, index_prefix, max_size)

    if messages:
        communication = get_messages_str(messages)
        dialect = get_dialect(messages)
        dialect_str = get_dialect_str(dialect)

        report = {
            "communication": communication,
            "dialect": dialect_str}

        report["md5"], report["sha1"], report["sha256"], \
            report["sha512"], report["ssdeep"] = get_dialect_fingerprints(
                dialect)

        return report
