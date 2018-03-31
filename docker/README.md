## Overview
SpamScope has two Docker images on Docker Hub. These images are complete and they have both Apache Storm and SpamScope with all requirements:
 - [spamscope-deps](https://hub.docker.com/r/fmantuano/spamscope-deps/): you should use this image as base of all SpamScope images. This image doesn't have SpamScope, but has all its requirements.
 - [spamscope-elasticsearch](https://hub.docker.com/r/fmantuano/spamscope-elasticsearch/): this image is an example of image that use Elasticsearch as database store.

 ## How make a custom image
 The `Dockerfile` example in this repository start with:

 ```
 FROM fmantuano/spamscope-deps
 ...
 ```

 All images should start with this `FROM`, that is a base image with all SpamScope requirements.

 Then you can clone official SpamScope repository:

 ```
 ...
ARG SPAMSCOPE_VER="develop"
ENV SPAMSCOPE_CONF_FILE="/etc/spamscope/spamscope.yml" \
    SPAMSCOPE_PATH="/opt/spamscope"
 ...
RUN git clone -b ${SPAMSCOPE_VER} --single-branch https://github.com/SpamScope/spamscope.git ${SPAMSCOPE_PATH};
 ...
 ```

It's very important set `SPAMSCOPE_CONF_FILE` environment varible, that SpamScope uses to find the main configuration file.

After that you can build your image:

```
$ docker build -t spamscope-debug .
```

##  Example
In this repository there is an example of `Dockerfile` that can be used for debug.

I don't like use `docker` command, so I made a `docker-compose.yml` that is more clean and easy to use.

The `docker-compose.yml` example uses `spamscope-debug` image, if doesn't exist, builds it. I want to analyze the followings lines:

```
volumes:
      - ${HOST_SPAMSCOPE_CONF}:/etc/spamscope
      - ${HOST_MAILS_FOLDER}:${DOCKER_MAILS_FOLDER}
```

With `volumes` you mount host folders in docker container folders. In this case `HOST_SPAMSCOPE_CONF` is the folder with SpamScope configuration, `HOST_MAILS_FOLDER` is the folder with emails to analyze and `DOCKER_MAILS_FOLDER` the email folder in docker container.

It's very important the main configuration file, that it's related to docker container.

Now we have a new `Dockerfile`, a new `docker-compose.yml` and a complete configuration file (`SPAMSCOPE_CONF_FILE`), so we can start Apache Storm:

```
$ cd docker
$ sudo docker-compose up -d
```

After any seconds Apache Storm will be up and running, you can test the url `http://localhost:8080`.

But SpamScope isn't up because you must submit a topology. From Apache Storm concepts:

_The logic for a realtime application is packaged into a Storm topology. A Storm topology is analogous to a MapReduce job. One key difference is that a MapReduce job eventually finishes, whereas a topology runs forever (or until you kill it, of course). A topology is a graph of spouts and bolts that are connected with stream groupings._

Now we can submit the `spamscope_debug` topology inside the docker container `spamscope-debug` using a custom command line tool that comes with SpamScope `spamscope-topology`.

```
$ docker-compose exec -d -T spamscope-debug spamscope-topology submit -g spamscope_debug -p 100 -t 30
```

The first part of this command is related to `docker-compose`:

```
docker-compose exec -d -T spamscope-debug
```

and it says: _exec my command in container spamscope-debug_.

The command that I want to exec is `spamscope-topology submit`, for more details read the guide inside [spamscope/src/cli/](../src/cli/README.md) folder.

Now SpamScope is up and running. You can navigate url `http://localhost:8080` and you will see `spamscope_debug` under `Topology Summary` section.