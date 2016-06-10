#!/usr/bin/env python

import logging
import pika


log = logging.getLogger(__name__)


class RabbitConnectionFailed(Exception):
    pass


class RabbitChannelFailed(Exception):
    pass


class RabbitPushMessageFailed(Exception):
    pass


class Rabbit:

    def rabbit_connection(self, server, user, password):
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
            log.exception(
                "Failed rabbit connection to server {}".format(
                    self._rabbit_server
                )
            )
            raise RabbitConnectionFailed(
                "Failed rabbit connection to server {}".format(
                    self._rabbit_server
                )
            )

    def rabbit_channel(self, connection, queue):
        try:
            channel = connection.channel()
            channel.queue_declare(
                queue=queue,
                durable=True,
            )
            return channel
        except:
            log.exception("Failed creation channel {}".format(queue))
            raise RabbitChannelFailed(
                "Failed creation channel {}".format(queue)
            )

    def rabbit_push_message(self, channel, queue, message):
        try:
            channel.basic_publish(
                exchange='',
                routing_key=queue,
                body=message,
                properties=pika.BasicProperties(delivery_mode=2)
            )
        except:
            log.exception("Failed pushing message in queue")
            raise RabbitPushMessageFailed("Failed pushing message in queue")

    def rabbit_get_message(self, channel, queue):
        try:
            method_frame, header_frame, message = channel.basic_get(
                queue=queue
            )
            return method_frame, header_frame, message
        except:
            log.exception("Failed getting message from queue {}".format(queue))
            return

    def rabbit_acknowledge_message(self, channel, delivery_tag):
        try:
            channel.basic_ack(delivery_tag)
        except:
            log.exception(
                "Failed ack for delivery_tag {}".format(delivery_tag)
            )

    def rabbit_close_connection(self, connection):
        try:
            connection.close()
        except:
            log.exception("Failed close Rabbit connection")

    def rabbit_close_channel(self, channel):
        try:
            channel.close()
        except:
            log.exception("Failed close Rabbit channel")
