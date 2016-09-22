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
from spout.files_mails import FilesMailSpout


class OutputDebugTopology(Topology):
    files_spout = FilesMailSpout.spec(
        name="files-mails")

    tokenizer = Tokenizer.spec(
        name="tokenizer",
        inputs=[files_spout],
        par=2)

    attachments = Attachments.spec(
        name="attachments",
        inputs={tokenizer: Grouping.fields('sha256_random')},
        par=2)

    urls_body = UrlsHandlerBody.spec(
        name="urls-handler-body",
        inputs={tokenizer: Grouping.fields('sha256_random')})

    urls_attachments = UrlsHandlerAttachments(
        name="urls-handler-attachments",
        inputs={attachments: Grouping.fields('sha256_random')})

    phishing = Phishing.spec(
        name="phishing",
        inputs={
            tokenizer: Grouping.fields('sha256_random'),
            attachments: Grouping.fields('sha256_random'),
            urls_body: Grouping.fields('sha256_random'),
            urls_attachments: Grouping.fields('sha256_random')})

    forms = Forms.spec(
        name="forms",
        inputs={tokenizer: Grouping.fields('sha256_random')})

    json = JsonMaker.spec(
        name="json",
        inputs={
            tokenizer: Grouping.fields('sha256_random'),
            phishing: Grouping.fields('sha256_random'),
            attachments: Grouping.fields('sha256_random'),
            forms: Grouping.fields('sha256_random'),
            urls_body: Grouping.fields('sha256_random'),
            urls_attachments: Grouping.fields('sha256_random')})

    output_debug = OutputDebug.spec(
        name="output-debug",
        inputs=[json])
