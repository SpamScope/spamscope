![SpamScope](https://raw.githubusercontent.com/SpamScope/spamscope/develop/docs/logo/spamscope.png)


## Overview
SpamScope comes with some tools that help you to manage it:
  - spamscope-topology
  - spamscope-elasticsearch


## spamscope-topology

General options:

```
usage: spamscope-topology [-h] [-p PATH] [-v] {submit} ...

It manages SpamScope topologies

positional arguments:
  {submit}              sub-commands
    submit              Submit a SpamScope Storm topology to Nimbus.

optional arguments:
  -h, --help            show this help message and exit
  -p PATH, --path PATH  SpamScope main path. (default: /opt/spamscope)
  -v, --version         show program's version number and exit
```

Submit options:

```
usage: spamscope-topology submit [-h]
                                 [-g {spamscope_debug,spamscope_elasticsearch,spamscope_redis}]
                                 [-w WORKERS] [-k TICK] [-p MAX_PENDING]
                                 [-s SPOUT_SLEEP] [-t TIMEOUT]

optional arguments:
  -h, --help            show this help message and exit
  -g {spamscope_debug,spamscope_elasticsearch,spamscope_redis}, --topology {spamscope_debug,spamscope_elasticsearch,spamscope_redis}
                        SpamScope topology.
  -w WORKERS, --workers WORKERS
                        Apache Storm workers for your topology.
  -k TICK, --tick TICK  Every tick seconds SpamScope configuration is
                        reloaded.
  -p MAX_PENDING, --max-pending MAX_PENDING
                        This value puts a limit on how many mails can be in
                        flight.
  -s SPOUT_SLEEP, --spout_sleep SPOUT_SLEEP
                        Max sleep in ms for emit new mail in topology.
  -t TIMEOUT, --timeout TIMEOUT
                        How long (in s) between heartbeats until supervisor
                        considers that worker dead.
```


## spamscope-elasticsearch

General options:

```
usage: spamscope-elasticsearch [-h] [-c CLIENT_HOST] [-m MAX_RETRY] [-v]
                               {replicas,template,get-payload} ...

It manages SpamScope topologies

positional arguments:
  {replicas,template,get-payload}
                        sub-commands
    replicas            Update the number of replicas
    template            Update/add template
    get-payload         Get sample payload from Elasticsearch

optional arguments:
  -h, --help            show this help message and exit
  -c CLIENT_HOST, --client-host CLIENT_HOST
                        Elasticsearch client host (default: elasticsearch)
  -m MAX_RETRY, --max-retry MAX_RETRY
                        Max retry for action (default: 10)
  -v, --version         show program's version number and exit
```

Replicas options:

```
usage: spamscope-elasticsearch replicas [-h] [-n NR_REPLICAS] [-i INDEX]

optional arguments:
  -h, --help            show this help message and exit
  -n NR_REPLICAS, --nr-replicas NR_REPLICAS
                        Number of replicas.
  -i INDEX, --index INDEX
                        A comma-separated list of index names; use _all or
                        empty string to perform the operation on all indices.
```

Template options:

```
usage: spamscope-elasticsearch template [-h] -p TEMPLATE_PATH -n TEMPLATE_NAME

optional arguments:
  -h, --help            show this help message and exit
  -p TEMPLATE_PATH, --template-path TEMPLATE_PATH
                        Path of template.
  -n TEMPLATE_NAME, --template-name TEMPLATE_NAME
                        Template name
```

Get payload options
```
usage: spamscope-elasticsearch get-payload [-h] [-i INDEX] -a HASH_VALUE -f
                                           FILE_OUTPUT

optional arguments:
  -h, --help            show this help message and exit
  -i INDEX, --index INDEX
                        A comma-separated list of index names; use _all or
                        empty string to perform the operation on all indices.
  -a HASH_VALUE, --hash-value HASH_VALUE
                        Sample hash to get
  -f FILE_OUTPUT, --file-output FILE_OUTPUT
                        File output
```
