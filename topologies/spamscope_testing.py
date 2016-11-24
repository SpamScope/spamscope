#!/usr/bin/env python
# -*- coding: utf-8 -*-


from streamparse import Grouping, Topology

from bolts.attachments import Attachments
from bolts.forms import Forms
from bolts.json_maker import JsonMaker
from bolts.output_debug import OutputDebug
from bolts.phishing import Phishing
from bolts.tokenizer import Tokenizer
from bolts.urls_handler_attachments import UrlsHandlerAttachments
from bolts.urls_handler_body import UrlsHandlerBody
from spouts.files_mails import FilesMailSpout


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
        par=1)

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

    output_debug = OutputDebug.spec(
        name="output-debug",
        inputs=[json])
