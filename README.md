[![PyPI version](https://badge.fury.io/py/SpamScope.svg)](https://badge.fury.io/py/SpamScope)
[![Build Status](https://travis-ci.org/SpamScope/spamscope.svg?branch=master)](https://travis-ci.org/SpamScope/spamscope)
[![Coverage Status](https://coveralls.io/repos/github/SpamScope/spamscope/badge.svg?branch=develop)](https://coveralls.io/github/SpamScope/spamscope?branch=develop)
[![BCH compliance](https://bettercodehub.com/edge/badge/SpamScope/spamscope?branch=develop)](https://bettercodehub.com/)

![SpamScope](https://raw.githubusercontent.com/SpamScope/spamscope/develop/docs/logo/spamscope.png)

# Overview
SpamScope is an advanced spam analysis tool that use [Apache Storm](http://storm.apache.org/) with [streamparse](https://github.com/Parsely/streamparse) to process a stream of mails.
To understand how SpamScope works, I suggest to read these overviews:
 - [Apache Storm Concepts](http://storm.apache.org/releases/1.2.1/Concepts.html)
 - [Streamparse Quickstart](http://streamparse.readthedocs.io/en/stable/quickstart.html)

In general the first step is start Apache Storm, then you can run the topologies.
SpamScope has some topologies in [topologies folder](./topologies/), but you can make others topologies.

![Schema topology](docs/images/schema_topology.png?raw=true "Schema topology")

# Why should I use SpamScope
- It's very fast: the job is splitted in functionalities that work in parallel.
- It's flexible: you can choose what SpamScope has to do.
- It's distributed: SpamScope uses Apache Storm, free and open source distributed realtime computation system.
- It makes JSON output that you can save where you want.
- It's easy to setup: there are docker images and docker-compose ready for use.
- It's integrated with Apache Tika, VirusTotal, Thug, Shodan and SpamAssassin (for now).
- It's free and open source (for special functions you can contact me).
- It can analyze Outlook msg.

## Distributed
SpamScope uses Apache Storm that allows you to start small and scale horizontally as you grow. Simply add more workers.

## Flexibility
You can choose your mails input sources (with **spouts**) and your functionalities (with **bolts**).

SpamScope comes with the following bolts:
 - **tokenizer** splits mail in token like headers, body, attachments and it can filter emails, attachments and ip addresses already seen
 - **phishing** looks for your keywords in email and connects email to targets (bank, your customers, etc.)
 - **raw_mail** is for all third party tools that analyze raw mails like SpamAssassin
 - **attachments** analyzes all mail attachments and uses third party tools like VirusTotal
 - **network** analyzes all sender ip addresses with third party tools like Shodan
 - **urls** extracts all urls in email and attachments
 - **json_maker** and **outputs** make the json report and save it

## Store where you want
You can build your custom output bolts and store your data in Elasticsearch, MongoDB, filesystem, etc.

## Build your topology
With streamparse tecnology you can build your topology in Python, add and/or remove spouts and bolts.

## API
For now SpamScope doesn't have its own API, because it isn't tied to any tecnology.
If you use `Redis` as spout (input), you'll use Redis API to put mails in topology.
If you use `Elasticsearch` as output, you'll use Elasticsearch API to get results.

It's possible to develop a middleware API that it talks with input, output and changes the configuration, but now there isn't.

# Apache 2 Open Source License
SpamScope can be downloaded, used, and modified free of charge. It is available under the Apache 2 license.

[![Donate](https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif "Donate")](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=VEPXYP745KJF2)

# SpamScope on Web
 - [Shodan Applications & Integrations](https://developer.shodan.io/apps)
 - [The Honeynet Project](http://honeynet.org/node/1329)
 - [securityonline.info](http://securityonline.info/pcileech-direct-memory-access-dma-attack-software/)
 - [jekil/awesome-hacking](https://github.com/jekil/awesome-hacking)

# Authors

## Main Author
 Fedele Mantuano (**LinkedIn**: [Fedele Mantuano](https://www.linkedin.com/in/fmantuano/))

# Requirements
For operating system requirements you can read `Ansible` playbook, that goes into details.

For Python requirements you can read:
 * [mandatory requirements](./requirements.txt)
 * [optional requirements](./requirements_optional.txt)

_Thug_ is another optional requirement. See Thug section for more details.

## Apache Storm
[Apache Storm](http://storm.apache.org/) is a free and open source distributed realtime computation system.

## streamparse
[streamparse](https://github.com/Parsely/streamparse) lets you run Python code against real-time streams of data via Apache Storm.

## mail-parser
[mail-parser](https://github.com/SpamScope/mail-parser) is the parsing for raw email of SpamScope.

## Faup
[Faup](https://github.com/stricaud/faup) stands for Finally An Url Parser and is a library and command line tool to parse URLs and normalize fields.

## rarlinux (optional)
[rarlinux](https://www.rarlab.com/) unarchives rar file.

## SpamAssassin (optional)
SpamScope can use [SpamAssassin](http://spamassassin.apache.org/) an open source anti-spam to analyze every mails.

## Apache Tika (optional)
SpamScope can use [Apache Tika](https://tika.apache.org/) to parse every attachments.
The Apache Tika toolkit detects and extracts metadata and text from over a thousand different file types (such as PPT, XLS, and PDF).
To use Apache Tika in SpamScope you must install [tika-app-python](https://github.com/fedelemantuano/tika-app-python) with `pip` and [Apache Tika](https://tika.apache.org/download.html).

## Thug (optional)
From release v1.3 SpamScope can analyze Javascript and HTML attachments with [Thug](https://github.com/buffer/thug).
If you want to analyze the attachments with Thug, follow [these instructions](http://buffer.github.io/thug/doc/build.html) to install it. Enable it in `attachments` section.

What is Thug? From README project:
> Thug is a Python low-interaction honeyclient aimed at mimicing the behavior of a web browser in order to detect and emulate malicious contents.

You can see a complete SpamScope report with Thug analysis [here](https://goo.gl/Y4kWCv).

Thug analysis can be very slow and you can have `heartbeat timeout` in Apache Storm.
To avoid any issue set `supervisor.worker.timeout.secs`:

```
nr. user agents * timeout_thug < supervisor.worker.timeout.secs
```

The best value for `threshold` is 1.

## VirusTotal (optional)
It's possible add to results (for mail attachments and sender ip address) the VirusTotal report. You need a private API key.

## Shodan (optional)
It's possible add to results the Shodan report for sender ip address. You need a private API key.

## Elasticsearch (optional)
It's possible to store the results in Elasticsearch. In this case you should install `elasticsearch` package.

## Redis (optional)
It's possible to store the results in Redis. In this case you should install `redis` package.

# Configuration
Read the [example configuration file](./conf/spamscope.example.yml).
The default value where SpamScope will search the configuration file is `/etc/spamscope/spamscope.yml`, but it's possible to set the environment variable `SPAMSCOPE_CONF_FILE`:

```
$ export SPAMSCOPE_CONF_FILE=/etc/spamscope/spamscope.yml
```

# Installation
You can use:
  * [Docker images](./docker/README.md) to run SpamScope with docker engine
  * [Ansible](./ansible/README.md): to install and run SpamScope on server

# Topologies
SpamScope comes with three topologies:
   - [spamscope_debug](./topologies/spamscope_debug.py): the output are JSON files on file system.
   - [spamscope_elasticsearch](./topologies/spamscope_elasticsearch.py): the output are stored in Elasticsearch indexes.
   - [spamscope_redis](./topologies/spamscope_redis.py): the output are stored in Redis.

If you want submit SpamScope topology use `spamscope-topology submit` tool. For more details [see SpamScope cli tools](src/cli/README.md):

```
$ spamscope-topology submit --topology {spamscope_debug,spamscope_elasticsearch,spamscope_redis}
```

It's possible to change the default settings for all Apache Storm options. I suggest to change these options:

 - **topology.tick.tuple.freq.secs**: reload configuration of all bolts
 - **topology.max.spout.pending**: Apache Storm framework will then throttle your spout as needed to meet the `topology.max.spout.pending` requirement
 - **topology.sleep.spout.wait.strategy.time.ms**: max sleep for emit new tuple (mail)

You can use `spamscope-topology submit` to do these changes.

# Important
If you are using Elasticsearch output, I suggest you to use [Elasticsearch templates](./conf/templates) that comes with SpamScope.

# Unittest
SpamScope comes with unittests for each modules. In bolts and spouts there are no special features, all intelligence is in external modules.
All unittests are in [tests folder](tests/).

To have complete tests you should set the followings enviroment variables:

```
$ export THUG_ENABLED=True
$ export VIRUSTOTAL_ENABLED=True
$ export VIRUSTOTAL_APIKEY="your key"
$ export ZEMANA_ENABLED=True
$ export ZEMANA_APIKEY="your key"
$ export ZEMANA_PARTNERID="your partner id"
$ export ZEMANA_USERID="your userid"
$ export SHODAN_ENABLED=True
$ export SHODAN_APIKEY="your key"
$ export SPAMASSASSIN_ENABLED=True
```

# Output example
This is a [raw email](https://goo.gl/wMBfbF) that I analyzed with SpamScope:
  - [SpamScope output](https://goo.gl/fr4i7C).

This is another example with [Thug analysis](https://goo.gl/Y4kWCv).

# Screenshots
![Apache Storm](docs/images/Docker00.png?raw=true "Apache Storm")

![SpamScope](docs/images/Docker01.png?raw=true "SpamScope")

![SpamScope Topology](docs/images/Docker02.png?raw=true "SpamScope Topology")

![SpamScope Map](docs/images/map.png?raw=true "SpamScope Map")
