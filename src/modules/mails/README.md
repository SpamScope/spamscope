# Overview
This package contains all post processing modules that analyze the raw mails:
 - SpamAssassin
 - SMTP dialect analysis

# SpamAssassin
**module name**: spamassassin

This module analyzes the raw mail with SpamAssassin and returns a report with the following keys:

```
"X-Spam-Checker-Version"
"X-Spam-Flag"
"X-Spam-Level"
"X-Spam-Status"
"score"
"details"
```

This processing is very slow. Use only if you need it.

# SMTP dialect analysis
**module name**: dialect

If you want to know, what the **SMTP dialect** is, you should read [this article](https://sissden.eu/blog/analysis-of-smtp-dialects).
To explain SMTP dialect is out of scope. I will explain how SpamScope analyzes it.

## Requirements
This module works only if you have the logs of `Postfix` SMTP server, related the emails that you are ingesting, stored in `Elasticsearch`. You should use pipeline and postfix patterns saved [here](../../../conf/logstash/).

The logs of Postfix server must be in verbose mode (see [here](http://www.postfix.org/DEBUG_README.html#verbose)), to log also the communication from client and server.

## How it works
SpamScope from the `message-id` header, gets the communication from client and server:

```
server: 220 localhost ESMTP Postfix
client: HELO test.com
server: 250 localhost
client: MAIL FROM:<3136652305@hh.com>
server: 250 2.1.0 Ok
client: RCPT TO:<cyndy@dest.com>
server: 250 2.1.5 Ok
server: 354 End data with <CR><LF>.<CR><LF>
client: DATA
server: 250 2.0.0 Ok: queued as 6D5F867001B
server: 221 2.0.0 Bye
client: Quit
```

Then it extracts from it only the client commands:

```
HELO  MAIL FROM: RCPT TO: DATA Quit
```

After that calculates the fingerprintings of client commands. These fingerprints are useful to detect groups of clients that are using the same commands format.