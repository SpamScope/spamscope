# Overview
In this folder there are all SpamScope `spouts`.

# How add a new spout
These are the steps to add a new `spout` to Spamscope:

 - add a new module in [spouts](./) folder. This module should implement a new class that has `AbstractSpout` as base.

 - import the new class in [__init__.py](./__init__.py)

 - add the new section in [main configuration file](../../conf/spamscope.example.yml). The name of this section will be used in topology file

 - add the new spout in [topology](../../topologies) 