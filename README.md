[![Build Status](https://travis-ci.org/SpamScope/spamscope.svg?branch=master)](https://travis-ci.org/SpamScope/spamscope)
[![Coverage Status](https://coveralls.io/repos/github/SpamScope/spamscope/badge.svg?branch=develop)](https://coveralls.io/github/SpamScope/spamscope?branch=develop)
[![BCH compliance](https://bettercodehub.com/edge/badge/SpamScope/spamscope?branch=develop)](https://bettercodehub.com/)

![SpamScope](https://raw.githubusercontent.com/SpamScope/spamscope/develop/docs/logo/spamscope.png)


## Overview
SpamScope is an advanced spam analysis tool that use [Apache Storm](http://storm.apache.org/) with [streamparse](https://github.com/Parsely/streamparse) to process a stream of mails. 

It's possible to analyze more than 5 milions of mails for day with a 4 cores server and 4 GB of RAM (without third party analysis). 

![Schema topology](docs/images/schema_topology.png?raw=true "Schema topology")

### Why should I use SpamScope
- It's very fast: the job is splitted in functionalities that work in parallel.
- It's flexible: you can choose what SpamScope has to do.
- It's distributed: SpamScope uses Apache Storm, free and open source distributed realtime computation system.
- It makes JSON output that you can save where you want.
- It's easy to setup: there are docker images and docker-compose ready for use.
- It's integrated with Apache Tika, VirusTotal, Thug, Shodan and SpamAssassin (for now).
- It's free and open source (for special functions you can contact me).

### Distributed
SpamScope uses Apache Storm that allows you to start small and scale horizontally as you grow. Simply add more workers.

### Flexibility
You can choose your mails input sources (with **spouts**) and your functionalities (with **bolts**). 

SpamScope comes with the following bolts: 
 - tokenizer splits mail in token like headers, body, attachments and it can filter emails, attachments and ip addresses already seen
 - phishing looks for your keywords in email and connects email to targets (bank, your customers, etc.)
 - raw_mail is for all third party tools that analyze raw mails like SpamAssassin
 - attachments analyzes all mail attachments and uses third party tools like VirusTotal
 - network analyzes all sender ip addresses with third party tools like Shodan
 - urls extracts all urls in email and attachments
 - json_maker and outputs make the json report and save it

### Store where you want
You can build your custom output bolts and store your data in Elasticsearch, MongoDB, filesystem, etc.

### Build your topology
With streamparse tecnology you can build your topology in Python, add and/or remove spouts and bolts.

### API
For now SpamScope doesn't have its own API, because it isn't tied to any tecnology.
If you use `Redis` as spout (input), you'll use Redis API to put mails in topology.
If you use `Elasticsearch` as output, you'll use Elasticsearch API to get results.

It's possible to develop a middleware API that it talks with input, output and changes the configuration, but now there isn't.

### Apache 2 Open Source License
SpamScope can be downloaded, used, and modified free of charge. It is available under the Apache 2 license.


[![Donate](https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif "Donate")](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=VEPXYP745KJF2)



## SpamScope on Web
 - [Shodan Applications & Integrations](https://developer.shodan.io/apps)
 - [The Honeynet Project](http://honeynet.org/node/1329)
 - [securityonline.info](http://securityonline.info/pcileech-direct-memory-access-dma-attack-software/)
 - [jekil/awesome-hacking](https://github.com/jekil/awesome-hacking)



## Output example
  - [Raw example email](https://goo.gl/wMBfbF).
  - [SpamScope output](https://goo.gl/MS7ugy).
  - [SpamScope complete output](https://goo.gl/fr4i7C).



## Authors

### Main Author
 Fedele Mantuano (**LinkedIn**: [Fedele Mantuano](https://www.linkedin.com/in/fmantuano/))



## Installation
For more details please visit the [wiki page](https://github.com/SpamScope/spamscope/wiki/Installation).

Clone repository

```
git clone https://github.com/SpamScope/spamscope.git
```

Enter in SpamScope directory install it:

```
pip install -r requirements.txt
python setup.py install
```

### Faup
[Faup](https://github.com/stricaud/faup) stands for Finally An Url Parser and is a library and command line tool to parse URLs and normalize fields.
To install it follow the [wiki](https://github.com/SpamScope/spamscope/wiki/Installation#faup).

### SpamAssassin (optional)
SpamScope can use [SpamAssassin](http://spamassassin.apache.org/) an open source anti-spam to analyze every mails.

### Tika (optional)
SpamScope can use [Tika App](https://tika.apache.org/) to parse every attachments.
The **Apache Tika** toolkit detects and extracts metadata and text from over a thousand different file types (such as PPT, XLS, and PDF).
To install it follow the [wiki](https://github.com/SpamScope/spamscope/wiki/Installation#tika-app-optional).
To enable Apache Tika analisys, you should set it in `attachments` section.

### Thug (optional)
From release v1.3 SpamScope can analyze Javascript and HTML attachments with [Thug](https://github.com/buffer/thug).
If you want to analyze the attachments with Thug, follow [these instructions](http://buffer.github.io/thug/doc/build.html) to install it and enable it in `attachments` section.

What is Thug? From README project:
```
Thug is a Python low-interaction honeyclient aimed at mimicing the behavior of a web browser in order to detect and emulate malicious contents.
```

You can see a complete SpamScope report with Thug analysis [here](https://goo.gl/Y4kWCv).

### VirusTotal (optional)
It's possible add to results (for mail attachments and sender ip address) the VirusTotal report. You need a private API key.

### Shodan (optional)
It's possible add to results the Shodan report for sender ip address. You need a private API key.

### Elasticsearch (optional)
It's possible to store the results in Elasticsearch. In this case you should install `elasticsearch` package.

### Redis (optional)
It's possible to store the results in Redis. In this case you should install `redis` package.



## Configuration
For more details please visit the [wiki page](https://github.com/SpamScope/spamscope/wiki/Configuration) or read the comments in the files in `conf` folder.

You can decide to **filter emails, attachments and ip addresses** already analyzed. All filters are in `tokenizer` bolt section.



## Usage
SpamScope comes with three topologies:
   - spamscope_debug (save json on file system)
   - spamscope_elasticsearch
   - spamscope_redis

and a general configuration file `spamscope.example.yml` in `conf/` folder.


If you want submit SpamScope topology use `spamscope-topology submit` tool. For more details `spamscope-topology submit -h`:

```
$ spamscope-topology submit --topology {spamscope_debug,spamscope_elasticsearch,spamscope_redis}
```


### Important
It's very important to set the main configuration file. The default value is `/etc/spamscope/spamscope.yml`, but it's possible to set the environment variable `SPAMSCOPE_CONF_FILE`:

```
$ export SPAMSCOPE_CONF_FILE=/etc/spamscope/spamscope.yml
```

If you use Elasticsearch output, I suggest you to use Elasticsearch template that comes with SpamScope.

### Apache Storm settings
It's possible change the default settings for all Apache Storm options. I suggest for SpamScope these options:

 - **topology.tick.tuple.freq.secs**: reload configuration of all bolts
 - **topology.max.spout.pending**: Apache Storm framework will then throttle your spout as needed to meet the `topology.max.spout.pending` requirement
 - **topology.sleep.spout.wait.strategy.time.ms**: max sleep for emit new tuple (mail)

For more details you can refer [here](http://streamparse.readthedocs.io/en/stable/quickstart.html).

To simplify this operation, SpamScope comes with a custom tool `spamscope-topology submit` where you can choose the values of all these parameters.



## Unittest
SpamScope comes with unittests for each modules. In bolts and spouts there are no special features, all intelligence is in external modules.
All unittests are in `tests` folder.

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


## Docker images
It's possible to use complete Docker images with Apache Storm and SpamScope. Take the following images:

 - [Root](https://hub.docker.com/r/fmantuano/spamscope-root/)
 - [Elasticsearch](https://hub.docker.com/r/fmantuano/spamscope-elasticsearch/)

For each image there are two tags: **develop** and **latest**.



## Screenshots
![Apache Storm](docs/images/Docker00.png?raw=true "Apache Storm")

![SpamScope](docs/images/Docker01.png?raw=true "SpamScope")

![SpamScope Topology](docs/images/Docker02.png?raw=true "SpamScope Topology")

![SpamScope Map](docs/images/map.png?raw=true "SpamScope Map")
