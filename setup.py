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

import os
import runpy
from setuptools import setup, find_packages


current = os.path.realpath(os.path.dirname(__file__))

with open(os.path.join(current, 'requirements.txt')) as f:
    requires = f.read().splitlines()

__version__ = runpy.run_path(
    os.path.join(current, "src", "options.py"))["__version__"]


setup(
    name="SpamScope",
    description="Fast Advanced Spam Analysis tool",
    license="Apache License, Version 2.0",
    url="https://github.com/SpamScope/spamscope",
    version=__version__,
    author="Fedele Mantuano",
    author_email="mantuano.fedele@gmail.com",
    maintainer="Fedele Mantuano",
    maintainer_email='mantuano.fedele@gmail.com',
    packages=find_packages(),
    platforms=["Linux"],
    keywords=["spam-analyzer", "email", "mail", "cli"],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.0",
        "Programming Language :: Python :: 3.1",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
    ],
    install_requires=requires,
    entry_points={'console_scripts': [
        "spamscope-topology = src.cli.spamscope_topology:main",
        "spamscope-elasticsearch = src.cli.spamscope_elasticsearch:main",
    ]},
)
