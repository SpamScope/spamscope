#!/usr/bin/env python
# -*- coding: utf-8 -*-


from streamparse import Grouping, Topology
from bolts import (Attachments, Forms, JsonMaker, OutputElasticsearch,
                   Phishing, Tokenizer, UrlsHandlerAttachments,
                   UrlsHandlerBody)
from spouts import FilesMailSpout


class OutputTestingTopology(Topology):
    files_spout = FilesMailSpout.spec(
        name="files-mails")

    tokenizer = Tokenizer.spec(
        name="tokenizer",
        inputs=[files_spout],
        par=1)

    attachments = Attachments.spec(
        name="attachments",
        inputs={tokenizer['attachments']: Grouping.fields('sha256_random')},
        par=4)

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

    json = JsonMaker.spec(
        name="json",
        inputs={
            tokenizer['mail']: Grouping.fields('sha256_random'),
            phishing: Grouping.fields('sha256_random'),
            attachments: Grouping.fields('sha256_random'),
            forms: Grouping.fields('sha256_random'),
            urls_body: Grouping.fields('sha256_random'),
            urls_attachments: Grouping.fields('sha256_random')})

    output_elasticsearch = OutputElasticsearch.spec(
        name="output-elasticsearch", inputs=[json], par=1)
