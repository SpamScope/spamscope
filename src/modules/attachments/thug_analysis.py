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

try:
    from modules import write_payload
except ImportError:
    from ...modules import write_payload

from .exceptions import ThugAnalysisFailed

try:
    from thug.ThugAPI import ThugAPI
except ImportError:
    raise ImportError(
        "Thug is not installed. Follow these instructions:"
        " http://buffer.github.io/thug/doc/build.html")

try:
    import simplejson as json
except ImportError:
    import json

log = logging.getLogger("Thug")


class ThugAnalysis(ThugAPI):
    def __init__(self):
        ThugAPI.__init__(self)

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
        local_file = write_payload(attachment["payload"],
                                   attachment["extension"])

        # Thug analysis
        for u in conf["user_agents"]:
            try:
                analysis = self.analyze(local_file, u, conf["referer"])
                results.append(analysis)
            except:
                msg = "Thug analysis failed for sample sha1 {!r}".format(
                    attachment["sha1"])
                log.error(msg)
                raise ThugAnalysisFailed(msg)
        else:
            try:
                os.remove(local_file)
            except OSError:
                pass

            return results

    def analyze(self, local_file, useragent="win7ie90",
                referer="http://www.google.com/"):
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

        # No console log
        self.set_log_quiet()

        # Enable JSON logging mode
        self.set_json_logging()

        # Initialize logging
        self.log_init(local_file)

        # Run analysis
        self.run_local(local_file)

        # Log analysis results
        self.log_event()

        return self.generate_json_report()
