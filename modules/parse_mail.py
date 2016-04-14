#!/usr/bin/env python
# -*- coding: utf-8 -*-

import email
import logging

log = logging.getLogger(__name__)


class ParseMail(object):

    """Class to tokenize mail. """

    def parse_from_file(self, fd):
        try:
            with open(fd) as mail:
                self._message = email.message_from_file(mail)
                self._parse()
        except:
            log.exception("Failed parsing mail from file")

    def parse_from_string(self, s):
        try:
            self._message = email.message_from_string(s)
            self._parse()
        except:
            log.exception("Failed parsing mail from string")

    def _parse(self):
        self._attachments = list()
        self._text_plain = list()

        for p in self._message.walk():
            if not p.is_multipart():
                filename = p.get_filename()
                if filename:
                    self._attachments.append(
                        {
                            "filename": filename,
                            "payload": p.get_payload(decode=True)
                        }
                    )
                else:
                    self._text_plain.append(p.get_payload(decode=True))

    @property
    def body(self):
        return "\n".join(self.text_plain)

    @property
    def header(self):
        return self._header

    @property
    def message_id(self):
        return self._message.get('message-id')

    @property
    def to_(self):
        return self._message.get('to', self._message.get('delivered-to'))

    @property
    def from_(self):
        return self._message.get('from')

    @property
    def subject(self):
        return self._message.get('subject')

    @property
    def text_plain(self):
        return self._text_plain

    @property
    def attachments(self):
        return self._attachments


if __name__ == '__main__':
    p = ParseMail()
