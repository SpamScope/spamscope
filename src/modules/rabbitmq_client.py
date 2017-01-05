#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Copyright 2016 Fedele Mantuano (https://twitter.com/fedelemantuano)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import pika


log = logging.getLogger(__name__)


class RabbitConnectionFailed(Exception):
    pass


class RabbitChannelFailed(Exception):
    pass


class RabbitPushMessageFailed(Exception):
    pass


class RabbitDeadLetterSetupFailed(Exception):
    pass


class Rabbit(object):

    @staticmethod
    def connection(server, user, password):
        credentials = pika.PlainCredentials(user, password)
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=server,
                    credentials=credentials,
                )
            )
            return connection
        except:
            message = "Failed rabbit connection to server {}".format(server)
            log.exception(message)
            raise RabbitConnectionFailed(message)

    @staticmethod
    def channel(connection, queue, arguments={}):
        try:
            channel = connection.channel()
            channel.queue_declare(
                queue=queue,
                durable=True,
                arguments=arguments,
            )
            return channel
        except:
            message = "Failed creation channel {}".format(queue)
            log.exception(message)
            raise RabbitChannelFailed(message)

    @staticmethod
    def deadletter_setup(
        connection,
        orig_queue,
        dl_exchange,
        dl_queue
    ):
        try:
            dlx_chan = connection.channel()
            dlx_chan.exchange_declare(exchange=dl_exchange, durable=True)
            dlx_result = dlx_chan.queue_declare(queue=dl_queue, durable=True)
            dlx_queue_name = dlx_result.method.queue
            dlx_chan.queue_bind(
                exchange=dl_exchange,
                routing_key=orig_queue,
                queue=dlx_queue_name)
            return dlx_chan
        except:
            message = "Failed dead-letter setup for orig_queue: {}, "
            "dl_exchange: {}, dl_queue: {}".format(
                orig_queue,
                dl_exchange,
                dl_queue)
            log.exception(message)
            raise RabbitDeadLetterSetupFailed(message)

    @staticmethod
    def push_message(channel, queue, message):
        try:
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except:
            message = "Failed pushing message in queue"
            log.exception(message)
            raise RabbitPushMessageFailed(message)

    @staticmethod
    def get_message(channel, queue):
        try:
            method_frame, header_frame, message = channel.basic_get(
                queue=queue
            )
            return method_frame, header_frame, message
        except:
            log.exception("Failed getting message from queue {}".format(queue))
            return

    @staticmethod
    def acknowledge_message(channel, delivery_tag):
        try:
            channel.basic_ack(delivery_tag)
        except:
            log.exception(
                "Failed ack for delivery_tag {}".format(delivery_tag)
            )

    @staticmethod
    def nack_message(channel, delivery_tag, requeue=False):
        try:
            channel.basic_nack(
                delivery_tag=delivery_tag,
                requeue=requeue,
            )
        except:
            log.exception(
                "Failed nack for delivery_tag {}".format(delivery_tag)
            )

    @staticmethod
    def close_connection(connection):
        try:
            connection.close()
        except:
            log.exception("Failed close Rabbit connection")

    @staticmethod
    def close_channel(channel):
        try:
            channel.close()
        except:
            log.exception("Failed close Rabbit channel")
