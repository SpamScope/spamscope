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

try:
    from elasticsearch import Elasticsearch
    from elasticsearch import ElasticsearchException
except ImportError:
    raise ImportError("To use dialects module, you must use Elasticsearch")

import datetime
import logging


log = logging.getLogger(__name__)


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
    """This function gets an Elastisearch index prefix
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


def get_dialect(message_id, servers, index_prefix):

    try:
        # get indices to query
        indices = get_elastic_indices(index_prefix)

        # connect to Elasticsearch
        es = Elasticsearch(hosts=servers)

        # From message_id get code of comunication from client and server
        r = es.search(
            index=indices, body=query_code % {"message_id": message_id})
        code = r["hits"]["hits"][0]["_source"]["code"]
        timestamp = r["hits"]["hits"][0]["_source"]["@timestamp"]
        log.debug("The code of {!r} is {!r}".format(message_id, code))

        # From code get client (ip and name)
        r = es.search(
            index=indices, body=query_client % {"code": code})
        client_ip = r["hits"]["hits"][0]["_source"]["client_ip"]
        client_name = r["hits"]["hits"][0]["_source"]["client_name"]

        # From client get dialects
        r = es.search(
            index=indices,
            body=query_dialect % {
                "timestamp": timestamp,
                "client_ip": client_ip,
                "client_name": client_name},
            size=100)
        dialects = [i["_source"]["dialect"] for i in r["hits"]["hits"]]

    except ElasticsearchException:
        log.exception(
            "Failed query Elasticsearch for dialect: {!r}".format(message_id))

    return dialects
