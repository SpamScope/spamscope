# Overview
In this folder there are all SpamScope topologies.
You will see that all topologies are same, except that changes where you store the JSON results.

The topologies `_iter` are more stable because use generator to send mails to bolts. They are RAM safe.

# spamscope_debug
In this topology the results are stored on file system. 

![Schema spamscope_debug](../docs/images/schema_spamscope_debug.png?raw=true "Schema spamscope_debug")

# spamscope_debug_iter
In this topology the results are stored on file system. It's same to `spamscope_debug` but it uses `iter-files-mails` spout.

# spamscope_elasticsearch
In this topology the results are stored in Elasticsearch. 

![Schema spamscope_elasticsearch](../docs/images/schema_spamscope_elasticsearch.png?raw=true "Schema spamscope_elasticsearch")

# spamscope_elasticsearch_iter
In this topology the results are stored in Elasticsearch. It's same to `spamscope_elasticsearch` but it uses `iter-files-mails` spout.

# spamscope_redis
In this topology the results are stored in Redis. 

![Schema spamscope_redis](../docs/images/schema_spamscope_redis.png?raw=true "Schema spamscope_redis")

# spamscope_redis_iter
In this topology the results are stored in Redis. It's same to `spamscope_redis` but it uses `iter-files-mails` spout.

![Schema spamscope_redis](../docs/images/schema_spamscope_redis.png?raw=true "Schema spamscope_redis")