#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from email.header import decode_header
import datetime
import email
import logging
import random
import string
import time

try:
    import simplejson as json
except ImportError:
    import json

log = logging.getLogger(__name__)


class InvalidMail(ValueError):
    pass


class NotUnicodeError(ValueError):
    pass


class InvalidDateMail(ValueError):
    pass


class FailedParsingDateMail(ValueError):
    pass


class MailParser(object):

    """Class to parse mail. """

    def parse_from_file(self, fd):
        with open(fd) as mail:
            self._message = email.message_from_file(mail)
            self._parse()

    def parse_from_string(self, s):
        self._message = email.message_from_string(s)
        self._parse()

    def _decode_header_part(self, header):
        output = u''

        for i in decode_header(header):
            if i[1]:
                output += unicode(i[0], i[1], errors='ignore').strip()
            else:
                output += unicode(i[0], errors='ignore').strip()

        if not isinstance(output, unicode):
            raise NotUnicodeError("Header part is not unicode")

        return output

    def _force_unicode(self, s):
        try:
            u = unicode(
                s,
                encoding=self.charset,
                errors='ignore',
            )
        except:
            u = unicode(
                s,
                errors='ignore',
            )

        if not isinstance(u, unicode):
            raise NotUnicodeError("Body part is not unicode")

        return u

    def _parse(self):
        if not self._message.keys():
            raise InvalidMail(
                "Mail without headers: {}".format(self._message.as_string())
            )

        self._attachments = list()
        self._text_plain = list()

        for p in self._message.walk():
            if not p.is_multipart():
                f = p.get_filename()
                if f:
                    filename = self._decode_header_part(f)
                    self._attachments.append(
                        {
                            "filename": filename,
                            "payload": p.get_payload(decode=False)
                        }
                    )
                else:
                    payload = self._force_unicode(
                        p.get_payload(decode=True),
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
        for k, v in self._message.items():
            v_u = self._decode_header_part(v)
            s += k + " " + v_u + "\n"
        return s

    @property
    def message_id(self):
        return self._decode_header_part(
            self._message.get('message-id', self.random_message_id)
        )

    @property
    def to_(self):
        return self._decode_header_part(
            self._message.get('to', self._message.get('delivered-to'))
        )

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

        if not date_:
            raise InvalidDateMail('Mail without date header')

        try:
            d = email.utils.parsedate(date_)
            t = time.mktime(d)
            return datetime.datetime.utcfromtimestamp(t)
        except:
            raise FailedParsingDateMail(
                'Failed parsing mail date: {}'.format(date_)
            )

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
        )

    @property
    def random_message_id(self):
        random_s = ''.join(random.choice(string.lowercase) for i in range(20))
        return "<" + random_s + "@nothing-message-id>"
