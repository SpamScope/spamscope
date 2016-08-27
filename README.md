# SpamScope

## Overview

SpamScope lets you run Python code against real-time streams of mails via [Apache Storm](http://storm.apache.org/). Use [streamparse](https://github.com/Parsely/streamparse) with which you can create Storm bolts (functionalities) and spouts (mails sources) in Python.

It's possible to analyze about 5 milions of mails (without Apache Tika analisys) for day with a 4 cores server and 4 GB of RAM. If you enable Apache Tika, you can analyze about 1 milion of mails.

![Schema topology](doc/images/schema_topology.png?raw=true "Schema topology")

## Example
[Here](https://gist.githubusercontent.com/fedelemantuano/5dd702004c25a46b2bd60de21e67458e/raw/3fdff560c2c6078c416b959ca74567ddcb5470d6/1471832668.1377_3.ivanova.orig) an example of raw mail and [here](https://gist.githubusercontent.com/fedelemantuano/e37095442263a51da7f5bd722532aab3/raw/b0c2b2094b4ecca4f1cb3cc3257ecae663ba84f4/1471832668.1377_3.ivanova.orig.json) the **SpamScope** analisys.

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


## Authors

### Main Author
 Fedele Mantuano (**Twitter**: [@fedelemantuano](https://twitter.com/fedelemantuano))


## Installation

Clone repository

```
git clone https://github.com/fedelemantuano/spamscope.git
```

Install requirements in file `requirements.txt` with `python-pip`:

```
pip install -r requirements.txt
```

There is another requirement [Faup](https://github.com/stricaud/faup). Install `faup` tool and then python library:

```
python setup.py install
```

## Docker image

It's possible to use a complete docker image with Apache Storm and SpamScope. Take it [here](https://hub.docker.com/r/fmantuano/spamscope/).


## Usage

If you want try it, you should copy `topologies/spamscope.example.clj` and add your functionalities (you can start with example), then you should change `spouts.conf` and `bolts.conf` options. The last variables point to two configuration files in YAML, like in `conf/components/`.

To run topology for debug:

```
sparse run --name topology
```

If you want submit topology to Apache Storm:

```
sparse submit -f --name topology
```

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

For submit these options:

```
sparse submit -f --name topology -o "topology.tick.tuple.freq.secs=60" -o "topology.max.spout.pending=100" -o "topology.sleep.spout.wait.strategy.time.ms=10"
```

For more details you can refer [here](http://streamparse.readthedocs.io/en/stable/quickstart.html).

### Apache Tika

It's possible add to results (for mail attachments) the output of [Apache Tika](https://tika.apache.org/) analysis. You should enable it in `attachments-bolt` section. SpamScope use Tika-app JAR with [tika-app](https://pypi.python.org/pypi/tika-app) python library.

### Virustotal

It's possible add to results (for mail attachments) Virustotal report. Maybe you need a private API key.
