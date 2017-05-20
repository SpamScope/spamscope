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


from streamparse import Grouping, Topology
from bolts import (Attachments, Forms, JsonMaker,
                   Phishing, Tokenizer, UrlsHandlerAttachments,
                   UrlsHandlerBody, Network, OutputRedis)
from spouts import FilesMailSpout


class OutputRedisTopology(Topology):

    files_spout = FilesMailSpout.spec(
        name="files-mails")

    tokenizer = Tokenizer.spec(
        name="tokenizer",
        inputs=[files_spout],
        par=1)

    attachments = Attachments.spec(
        name="attachments",
        inputs={tokenizer['attachments']: Grouping.fields('sha256_random')},
        par=2)

    urls_body = UrlsHandlerBody.spec(
        name="urls-handler-body",
        inputs={tokenizer['body']: Grouping.fields('sha256_random')})

    urls_attachments = UrlsHandlerAttachments.spec(
        name="urls-handler-attachments",
        inputs={attachments: Grouping.fields('sha256_random')})

    phishing = Phishing.spec(
        name="phishing",
        inputs={
            tokenizer['mail']: Grouping.fields('sha256_random'),
            attachments: Grouping.fields('sha256_random'),
            urls_body: Grouping.fields('sha256_random'),
            urls_attachments: Grouping.fields('sha256_random')})

    forms = Forms.spec(
        name="forms",
        inputs={tokenizer['body']: Grouping.fields('sha256_random')})

    network = Network.spec(
        name="network",
        inputs={tokenizer['network']: Grouping.fields('sha256_random')})

    json = JsonMaker.spec(
        name="json",
        inputs={
            tokenizer['mail']: Grouping.fields('sha256_random'),
            phishing: Grouping.fields('sha256_random'),
            attachments: Grouping.fields('sha256_random'),
            forms: Grouping.fields('sha256_random'),
            network: Grouping.fields('sha256_random'),
            urls_body: Grouping.fields('sha256_random'),
            urls_attachments: Grouping.fields('sha256_random')})

    output_redis = OutputRedis.spec(
        name="output-redis",
        inputs=[json])
