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


def generate_json_report():
    """
    Return JSON Thug report from logging
    """
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


class CustomWatchdog(Watchdog):
    def handler(self, signum, frame):
        """
        Function that handles Thug timeout
        """
        msg = "The analysis took more than {} seconds.".format(self.time)
        log.critical(msg)

        if self.callback:
            self.callback(signum, frame)

        log.ThugLogging.log_event()
        raise Exception(msg)


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

    def run(self, attachment, **conf):
        results = []

        # Parameters
        user_agents = conf.get("user_agents", [])
        referer = conf.get("referer", "http://www.google.com/")
        timeout = int(conf.get("timeout", 10))
        connect_timeout = int(conf.get("connect_timeout", 1))
        disable_cert_logging = conf.get("disable_cert_logging", True)
        disable_code_logging = conf.get("disable_code_logging", True)
        threshold = int(conf.get("threshold", 1))

        try:
            local_file = write_payload(
                attachment["payload"],
                attachment["extension"],
                attachment["content_transfer_encoding"])
        except KeyError:
            # If file is in archive it doesn't have content_transfer_encoding
            # keyword. In these cases content_transfer_encoding is base64
            local_file = write_payload(
                attachment["payload"],
                attachment["extension"])

        # Thug analysis
        for u in user_agents:
            analysis = self.analyze(
                local_file=local_file,
                connect_timeout=connect_timeout,
                disable_cert_logging=disable_cert_logging,
                disable_code_logging=disable_code_logging,
                referer=referer,
                threshold=threshold,
                timeout=timeout,
                useragent=u)
            results.append(analysis)
        else:
            try:
                os.remove(local_file)
            except OSError:
                pass

            return results

    def analyze(self,
                local_file,
                connect_timeout=1,
                disable_cert_logging=True,
                disable_code_logging=True,
                referer="http://www.google.com/",
                threshold=1,
                timeout=10,
                useragent="win7ie90",
                ):
        """ It performs the Thug analysis agaist a loca file

        Args:
            local_file (string): Local file (on filesystem) to analyze
            connect_timeout (int): Set the connect timeout
            disable_cert_logging (bool): Disable SSL/TLS certificate logging
            disable_code_logging (bool): Disable code logging
            referer (string): Referer to use for analysis
            threshold (int): Maximum pages to fetch
            timeout (int): Set the analysis timeout
            useragent (string): User agent to use for analysis

        Returns:
            Returns a Python object with the analysis
        """
        # Set useragent
        self.set_useragent(useragent)

        # Set referer
        self.set_referer(referer)

        # Set the analysis timeout
        self.set_timeout(timeout)

        # Maximum pages to fetch
        self.set_threshold(threshold)

        # Set the connect timeout
        self.set_connect_timeout(connect_timeout)

        # Disable code logging
        if disable_code_logging:
            self.disable_code_logging()

        # Disable SSL/TLS certificate logging
        if disable_cert_logging:
            self.disable_cert_logging()

        # No console log
        self.set_log_quiet()

        # Enable JSON logging mode
        self.set_json_logging()

        # Initialize logging
        self.log_init(local_file)

        try:
            # Run analysis
            # Analysis can go in timeout, in these cases is handled from
            # handler function
            self.run_local(local_file)

            # Log analysis results
            self.log_event()
        finally:
            return generate_json_report()
