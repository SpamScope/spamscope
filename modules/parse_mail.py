#!/usr/bin/env python
# -*- coding: utf-8 -*-

from email.header import decode_header
import datetime
import email
import json
import logging
import time

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

    def _decode_header_part(self, header):
        output = u''
        try:
            for i in decode_header(header):
                if i[1]:
                    output += unicode(i[0], i[1], errors='ignore').strip()
                else:
                    output += unicode(i[0], errors='ignore').strip()
            return output
        except:
            return header

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
                    payload = unicode(
                        p.get_payload(decode=True),
                        encoding=self.charset,
                        errors='ignore',
                    )
                    self._text_plain.append(payload)

        # Parsed object mail
        self._mail = {
            "attachments": self.attachments_list,
            "body": self.body,
            "date": self.date_mail,
            "from": self.from_,
            "headers": self.headers,
            "message_id": self.message_id,
            "subject": self.subject,
            "to": self.to_,
        }

    @property
    def body(self):
        return "\n".join(self.text_plain_list)

    @property
    def headers(self):
        s = ""
        for h in self._message.items():
            s += " ".join(h) + "\n"
        return s

    @property
    def message_id(self):
        return self._message.get('message-id')

    @property
    def to_(self):
        return self._message.get('to', self._message.get('delivered-to'))

    @property
    def from_(self):
        return self._decode_header_part(
            self._message.get('from')
        )

    @property
    def subject(self):
        return self._decode_header_part(
            self._message.get('subject')
        )

    @property
    def text_plain_list(self):
        return self._text_plain

    @property
    def attachments_list(self):
        return self._attachments

    @property
    def charset(self):
        return self._message.get_content_charset('utf-8')

    @property
    def date_mail(self):
        date_ = self._message.get('date')
        if date_:
            d = email.utils.parsedate(date_)
            t = time.mktime(d)
            return datetime.datetime.fromtimestamp(t)
        return None

    @property
    def parsed_mail_obj(self):
        return self._mail

    @property
    def parsed_mail_json(self):
        self._mail["date"] = self.date_mail.isoformat() \
            if self.date_mail else ""
        return json.dumps(
            self._mail,
            ensure_ascii=False,
            indent=None,
            sort_keys=True,
            encoding=self.charset,
        )


if __name__ == '__main__':
    p = ParseMail()
