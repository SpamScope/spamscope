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

import logging
import os
import tempfile
import sys

try:
    from modules import write_payload
except ImportError:
    from ...modules import write_payload

try:
    from thug.ThugAPI import ThugAPI
    from thug.ThugAPI.Watchdog import Watchdog
    from thug.DOM.DFT import DFT
except ImportError:
    raise ImportError(
        "Thug is not installed. Follow these instructions:"
        " http://buffer.github.io/thug/doc/build.html")

import PyV8
import simplejson as json


log = logging.getLogger("Thug")


class CustomWatchdog(Watchdog):
    def handler(self, signum, frame):
        msg = "The analysis took more than {} seconds.".format(self.time)
        log.critical(msg)

        if self.callback:
            self.callback(signum, frame)

        log.ThugLogging.log_event()
        raise BaseException(msg)


class ThugAnalysis(ThugAPI):
    def __init__(self):
        ThugAPI.__init__(self)

    def _ThugAPI__run(self, window):
        if log.Trace:
            sys.settrace(log.Trace)

        with PyV8.JSLocker():
            with CustomWatchdog(log.ThugOpts.timeout,
                                callback=self.watchdog_cb):
                dft = DFT(window)
                dft.run()

    def generate_json_report(self):
        if not log.ThugOpts.json_logging:
            return

        p = log.ThugLogging.modules.get('json', None)
        if p is None:
            return

        m = getattr(p, 'get_json_data', None)
        if m is None:
            return

        report = json.loads(m(tempfile.gettempdir()))
        return report

    def run(self, attachment, **conf):
        results = []

        try:
            local_file = write_payload(
                attachment["payload"], attachment["extension"],
                attachment["content_transfer_encoding"])
        except KeyError:
            # Path
            # If file is in archive it doesn't have content_transfer_encoding
            # keyword. In these cases content_transfer_encoding is base64
            local_file = write_payload(
                attachment["payload"], attachment["extension"])

        # Thug analysis
        for u in conf["user_agents"]:
            try:
                analysis = self.analyze(
                    local_file, u, conf["referer"], conf["timeout"])
                results.append(analysis)
            except UnicodeDecodeError:
                log.warning("UnicodeDecodeError for in Thug analysis")
        else:
            try:
                os.remove(local_file)
            except OSError:
                pass

            return results

    def analyze(self,
                local_file,
                useragent="win7ie90",
                referer="http://www.google.com/",
                timeout=5):
        """ It performs the Thug analysis agaist a loca file

        Args:
            local_file (string): Local file (on filesystem) to analyze
            useragent (string): User agent to use for analysis
            referer (string): Referer to use for analysis

        Returns:
            Returns a Python object with the analysis
        """
        # Set useragent
        self.set_useragent(useragent)

        # Set referer
        self.set_referer(referer)

        # Set timeout
        self.set_timeout(timeout)

        # No console log
        self.set_log_quiet()

        # Enable JSON logging mode
        self.set_json_logging()

        # Initialize logging
        self.log_init(local_file)

        # Run analysis
        try:
            self.run_local(local_file)
        finally:
            # catch timeout exception to get partial result

            # Log analysis results
            self.log_event()

            return self.generate_json_report()
