<p align="center"><img src="docs/logo/spamscope.jpg"/></p>


## Overview

SpamScope is an advanced spam analysis tool that use [Apache Storm](http://storm.apache.org/) with [streamparse](https://github.com/Parsely/streamparse) to process a stream of mails. 

It's possible to analyze about 5 milions of mails (without Apache Tika analisys) for day with a 4 cores server and 4 GB of RAM. If you enable Apache Tika, you can analyze about 1 milion of mails.

![Schema topology](docs/images/schema_topology.png?raw=true "Schema topology")

### Distributed
SpamScope use Apache Storm that allows you to start small and scale horizontally as you grow. Simply add more worker.

### Flexibility
You can chose your mails input sources (with spouts) and your functionalities (with bolts). SpamScope come with a tokenizer (split mail in token: headers, body, attachments), attachments and phishing analyzer (Which is the target of mails? Is there a malware in attachment?) and JSON output.

### Store where you want
You can build your custom output bolts and store your data in Elasticsearch, Mongo, filesystem, etc.

### Build your topology
With streamparse tecnology you can build your topology in Clojure, add and/or remove spouts and bolts.

### Apache 2 Open Source License
SpamScope can be downloaded, used, and modified free of charge. It is available under the Apache 2 license.
[![Donate](https://www.paypal.com/en_US/i/btn/btn_donateCC_LG.gif "Donate")](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=VEPXYP745KJF2)


## Output example
[Here](https://gist.githubusercontent.com/fedelemantuano/5dd702004c25a46b2bd60de21e67458e/raw/3fdff560c2c6078c416b959ca74567ddcb5470d6/1471832668.1377_3.ivanova.orig) an example of raw mail and [here](https://gist.githubusercontent.com/fedelemantuano/e37095442263a51da7f5bd722532aab3/raw/b0c2b2094b4ecca4f1cb3cc3257ecae663ba84f4/1471832668.1377_3.ivanova.orig.json) the **SpamScope** analisys output.


## Authors

### Main Author
 Fedele Mantuano (**Twitter**: [@fedelemantuano](https://twitter.com/fedelemantuano))


## Installation
For more details please visit [wiki page](https://github.com/SpamScope/spamscope/wiki/Installation).

Clone repository

```
git clone https://github.com/SpamScope/spamscope.git
```

Install requirements in file `requirements.txt` with `python-pip`:

```
pip install -r requirements.txt
```

There is another requirement: [Faup](https://github.com/stricaud/faup). Install `faup` tool and then python library with:

```
python setup.py install
```

## Configuration
All details are in `conf` folder.

From SpamScope v1.1 you can decide to **filter mails and attachments** already analyzed. If you enable filter in `tokenizer` section you will enable the RAM database and
SpamScope will check on it to decide if mail/attachment is already analyzed or not. If yes SpamScope will not analyze it and will store only the hashes.


## Usage

SpamScope comes with two topologies:
   - spamscope_debug
   - spamscope_elasticsearch

and a general configuration file `spamscope.conf` in `conf/` folder.


To run topology for debug:

```
sparse run --name topology
```

If you want submit topology to Apache Storm:

```
sparse submit -f --name topology
```

### Important
It's very importart pass configuration file to commands `sparse run` and `sparse submit`. There is an [open bug](https://github.com/Parsely/streamparse/issues/263) in streamparse:
  - `sparse run --name topology -o "spamscope_conf=/etc/spamscope/spamscope.yml"`
  - `sparse submit -f --name topology -o "spamscope_conf=/etc/spamscope/spamscope.yml"`

### Apache Storm settings

It's possible change the default setting for all Apache Storm options. I suggest for SpamScope these options:

 - **topology.tick.tuple.freq.secs**: reload configuration of all bolts
 - **topology.max.spout.pending**: Apache Storm framework will then throttle your spout as needed to meet the `topology.max.spout.pending` requirement
 - **topology.sleep.spout.wait.strategy.time.ms**: max sleep for emit new tuple (mail)

For SpamScope I tested these values to avoid failed tuples:

```
topology.tick.tuple.freq.secs: 60
topology.max.spout.pending: 100
topology.sleep.spout.wait.strategy.time.ms: 10
```

If Apache Tika is enabled:

```
topology.max.spout.pending: 10
```

For submit these options:

```
sparse submit -f --name topology -o "spamscope_conf=/etc/spamscope/spamscope.yml" -o "topology.tick.tuple.freq.secs=60" -o "topology.max.spout.pending=100" -o "topology.sleep.spout.wait.strategy.time.ms=10"
```

For more details you can refer [here](http://streamparse.readthedocs.io/en/stable/quickstart.html).

### Apache Tika

It's possible add to results (for mail attachments) the output of [Apache Tika](https://tika.apache.org/) analysis. You should enable it in `attachments` section. SpamScope use Tika-app JAR with [tika-app](https://pypi.python.org/pypi/tika-app) python library.

### Virustotal

It's possible add to results (for mail attachments) Virustotal report. Maybe you need a private API key.


## Docker image

It's possible to use a complete Docker image with Apache Storm and SpamScope. Take it [here](https://hub.docker.com/r/fmantuano/spamscope/). There are two tags: **latest** and **develop**.

![Apache Storm](docs/images/Docker00.png?raw=true "Apache Storm")

![SpamScope](docs/images/Docker01.png?raw=true "SpamScope")

![SpamScope Topology](docs/images/Docker02.png?raw=true "SpamScope Topology")
