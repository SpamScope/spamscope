#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

import os
import sys
import unittest

try:
    import simplejson as json
except ImportError:
    import json

base_path = os.path.realpath(os.path.dirname(__file__))
root = os.path.join(base_path, '..')
sys.path.append(root)
import src.modules.urls_extractor as urls_extractor


class TestUrlsExtractor(unittest.TestCase):
    extractor = urls_extractor.UrlsExtractor()

    body = u"""
     bla bla http://tweetdeck.twitter.com/ bla bla
     http://kafka.apache.org/documentation.html
     http://kafka.apache.org/documentation1.html
     bla bla bla https://docs.python.org/2/library/re.html bla bla
     bla bla bla https://docs.python.org/2/library/re_2.html> bla bla
     <p>https://tweetdeck.twitter.com/random</p> bla bla
     <p>https://tweetdeck.twitter.com/random_2</p>
    """

    body_not_unicode = """
     bla bla http://tweetdeck.twitter.com/ bla bla
     http://kafka.apache.org/documentation.html
     http://kafka.apache.org/documentation1.html
     bla bla bla https://docs.python.org/2/library/re.html bla bla
     bla bla bla https://docs.python.org/2/library/re_2.html> bla bla
     <p>https://tweetdeck.twitter.com/random</p> bla bla
     <p>https://tweetdeck.twitter.com/random_2</p>
    """

    body_unicode_error = u"""
    Return-Path: <>
    Delivered-To: umaronly@poormail.com
    Received: (qmail 15482 invoked from network); 29 Nov 2015 12:28:40 -0000
    Received: from unknown (HELO 112.149.154.61) (112.149.154.61)
      by smtp.customers.net with SMTP; 29 Nov 2015 12:28:40 -0000
      Received: from unknown (HELO localhost)
        (meghan3353839.5f10e@realiscape.com@110.68.103.81)
              by 112.149.154.61 with ESMTPA; Sun, 29 Nov 2015 21:29:24 +0900
              From: meghan3353839.5f10e@realiscape.com
              To: umaronly@poormail.com
              Subject: Gain your male attrctiveness

              Give satisfaction to your loved one
              http://contents.xn--90afavbplfx2a6a5b2a.xn--p1ai/

    """

    def test_body_unicode_error(self):
        self.extractor.extract(self.body_unicode_error)

        urls_obj = self.extractor.urls_obj
        self.assertIsInstance(urls_obj, dict)

        urls_json = self.extractor.urls_json
        self.assertIsInstance(urls_json, unicode)

        urls_obj = json.loads(urls_json)
        self.assertIsInstance(urls_obj, dict)

        self.assertIn('xn--90afavbplfx2a6a5b2a.xn--p1ai', urls_obj)

        url = urls_obj['xn--90afavbplfx2a6a5b2a.xn--p1ai'][0]['url']
        self.assertEqual(
            url,
            'http://contents.xn--90afavbplfx2a6a5b2a.xn--p1ai/'
        )

    def test_extractor(self):
        with self.assertRaises(urls_extractor.NotUnicodeError):
            self.extractor.extract(self.body_not_unicode)

        self.extractor.extract(self.body)
        results = self.extractor.urls_obj

        self.assertIsInstance(results, dict)

        self.assertIn('twitter.com', results)
        self.assertIsInstance(results['twitter.com'], list)
        self.assertEqual(len(results['twitter.com']), 3)

        self.assertIn('apache.org', results)
        self.assertIsInstance(results['apache.org'], list)
        self.assertEqual(len(results['apache.org']), 2)

        self.assertIn('python.org', results)
        self.assertIsInstance(results['python.org'], list)
        self.assertEqual(len(results['python.org']), 2)


if __name__ == '__main__':
    unittest.main()
