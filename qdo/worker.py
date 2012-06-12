# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
from contextlib import contextmanager
import os
import random
import time
import socket

from ujson import decode as ujson_decode

from qdo.config import ERROR_QUEUE
from qdo.config import STATUS_QUEUE
from qdo.partition import Partition
from qdo.queuey import QueueyConnection
from qdo.log import get_logger


@contextmanager
def dict_context():
    context = dict()
    try:
        yield context
    finally:
        del context


def default_failure(exc, context, queuey_conn):
    pass


def resolve(worker, section, name):
    if section[name]:
        mod, func_name = section[name].split(u':')
        result = __import__(mod, globals(), locals(), func_name)
        func = getattr(result, func_name)
        setattr(worker, name, func)


class Worker(object):
    """A Worker works on jobs.

    :param settings: Configuration settings
    :type settings: dict
    """

    def __init__(self, settings):
        self.settings = settings
        self.shutdown = False
        self.name = u'%s-%s' % (socket.getfqdn(), os.getpid())
        self.job = None
        self.job_context = dict_context
        self.job_failure = default_failure
        self.partition_policy = u'manual'
        self.partitions = {}
        self.configure()

    def configure(self):
        """Configure the worker based on the configuration settings.
        """
        qdo_section = self.settings.getsection(u'qdo-worker')
        self.wait_interval = qdo_section[u'wait_interval']
        resolve(self, qdo_section, u'job')
        resolve(self, qdo_section, u'job_context')
        resolve(self, qdo_section, u'job_failure')
        queuey_section = self.settings.getsection(u'queuey')
        self.queuey_conn = QueueyConnection(
            queuey_section[u'app_key'],
            connection=queuey_section[u'connection'])

    def configure_partitions(self, section):
        self.partition_policy = policy = section[u'policy']
        partition_ids = []
        queuey_conn = self.queuey_conn
        all_partitions = queuey_conn._partitions()
        if policy == u'manual':
            partition_ids = section[u'ids']
        elif policy == u'all':
            partition_ids = all_partitions

        def cond_create(queue_name):
            if queue_name + u'-1' not in all_partitions:
                queuey_conn.create_queue(queue_name=queue_name)
        cond_create(ERROR_QUEUE)
        cond_create(STATUS_QUEUE)
        self.assign_partitions(partition_ids)

    def track_partitions(self):
        status = {}
        # get all status messages, starting with the newest ones
        status_messages = self.queuey_conn.messages(
            STATUS_QUEUE, limit=100, order='descending')
        if len(status_messages) >= 100:
            # XXX deal with more than 100 status messages / partitions
            raise RuntimeError(u'More than 100 status messages detected!')
        for message in status_messages:
            body = ujson_decode(message[u'body'])
            partition = body[u'partition']
            if partition not in status:
                # don't overwrite newer messages with older status
                status[partition] = message[u'timestamp']
        return status

    def assign_partitions(self, partition_ids):
        for pid in list(self.partitions.keys()):
            if pid not in partition_ids:
                del self.partitions[pid]
        status = self.track_partitions()
        for pid in partition_ids:
            if pid.startswith((ERROR_QUEUE, STATUS_QUEUE)):
                continue
            self.partitions[pid] = Partition(
                self.queuey_conn, pid, msgid=status.get(pid, None))

    def work(self):
        """Work on jobs.

        This is the main loop of the worker.
        """
        if not self.job:
            return
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        partitions_section = self.settings.getsection(u'partitions')
        self.configure_partitions(partitions_section)
        atexit.register(self.stop)
        with self.job_context() as context:
            while 1:
                if self.shutdown:
                    break
                no_messages = 0
                for name, partition in self.partitions.items():
                    messages = partition.messages(limit=2)
                    if not messages:
                        no_messages += 1
                        continue
                    message = messages[0]
                    timestamp = message[u'timestamp']
                    try:
                        self.job(message, context)
                    except Exception as exc:
                        self.job_failure(exc, context, self.queuey_conn)
                    partition.timestamp = timestamp
                if no_messages == len(self.partitions):
                    self.wait()

    def wait(self):
        get_logger().incr(u'worker.wait_for_jobs')
        jitter = random.uniform(0.8, 1.2)
        time.sleep(self.wait_interval * jitter)

    def stop(self):
        """Stop the worker loop. Used in an `atexit` hook."""
        self.shutdown = True


def run(settings):
    worker = Worker(settings)
    worker.work()
