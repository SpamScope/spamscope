# SpamScope

## Overview

SpamScope lets you run Python code against real-time streams of mails via [Apache Storm](http://storm.apache.org/). Use [streamparse](https://github.com/Parsely/streamparse) with which you can create Storm bolts (functionalities) and spouts (mails sources) in Python. 

![Schema topology](doc/images/schema_topology.png?raw=true "Schema topology")

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

## Usage

If you want try it, you should copy `topologies/spamscope.example.clj` and add your functionalities (you can start with example), then you should change `spouts.conf` and `bolts.conf` parameters. The last variables point to two configuration files in YAML, like in `conf/components/`.

To run topology:

```
sparse run --name topology
```

For more details you can refer [here](http://streamparse.readthedocs.io/en/stable/quickstart.html).
