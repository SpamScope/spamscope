#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2017 Fedele Mantuano (https://twitter.com/fedelemantuano)

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

import argparse
import runpy
import os
import shlex
from subprocess import Popen, STDOUT


current = os.path.realpath(os.path.dirname(__file__))
__version__ = runpy.run_path(
    os.path.join(current, "..", "options.py"))["__version__"]


def get_args():
    parser = argparse.ArgumentParser(
        description="It manages SpamScope topologies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    subparsers = parser.add_subparsers(help="sub-commands", dest="subparser")

    # Common args
    parser.add_argument(
        "-p",
        "--path",
        default="/opt/spamscope",
        help="SpamScope main path.",
        dest="path")

    parser.add_argument(
        '-v',
        '--version',
        action='version',
        version='%(prog)s {}'.format(__version__))

    # Submit args
    submit = subparsers.add_parser(
        "submit", help="Submit a SpamScope Storm topology to Nimbus.")

    submit.add_argument(
        "-g",
        "--topology",
        choices=["spamscope_debug", "spamscope_elasticsearch",
                 "spamscope_redis"],
        default="debug",
        help="SpamScope topology.",
        dest="topology")

    submit.add_argument(
        "-e",
        "--environment",
        default="prod",
        help="The environment to use for the command.",
        dest="environment")

    submit.add_argument(
        "-w",
        "--workers",
        default=1,
        type=int,
        help="Apache Storm workers for your topology.",
        dest="workers")

    submit.add_argument(
        "-k",
        "--tick",
        default=60,
        type=int,
        help="Every tick seconds SpamScope configuration is reloaded.",
        dest="tick")

    submit.add_argument(
        "-p",
        "--max-pending",
        default=200,
        type=int,
        help="This value puts a limit on how many mails can be in flight.",
        dest="max_pending")

    submit.add_argument(
        "-s",
        "--spout_sleep",
        default=10,
        type=int,
        help="Max sleep in ms for emit new mail in topology.",
        dest="spout_sleep")

    submit.add_argument(
        "-t",
        "--timeout",
        default=45,
        type=int,
        help=("How long (in s) between heartbeats until supervisor considers "
              "that worker dead."),
        dest="timeout")

    return parser.parse_args()


def create_jar():
    pass


def submit_topology(topology, environment, nr_worker, tick,
                    max_pending, spout_sleep, timeout):
    command_line = (
        "sparse submit -f -n {topology} -w {nr_worker} -e {environment} "
        "-o topology.tick.tuple.freq.secs={tick} "
        "-o topology.max.spout.pending={max_pending} "
        "-o topology.sleep.spout.wait.strategy.time.ms={spout_sleep} "
        "-o supervisor.worker.timeout.secs={timeout} "
        "-o topology.message.timeout.secs={timeout}".format(
            topology=topology, environment=environment, nr_worker=nr_worker,
            tick=tick, max_pending=max_pending, spout_sleep=spout_sleep,
            timeout=timeout))

    args = shlex.split(command_line)
    proc = Popen(args, stderr=STDOUT)
    _, _ = proc.communicate()


def main():
    # Command line args
    args = get_args()

    # Change work directory
    os.chdir(args.path)

    if args.subparser == "submit":
        submit_topology(
            topology=args.topology,
            environment=args.environment,
            nr_worker=args.workers,
            tick=args.tick,
            max_pending=args.max_pending,
            spout_sleep=args.spout_sleep,
            timeout=args.timeout)


if __name__ == "__main__":
    main()
