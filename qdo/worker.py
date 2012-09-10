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

from kazoo.client import KazooClient
from queuey_py import Client
from ujson import decode as ujson_decode
from ujson import encode as ujson_encode

from qdo.config import ERROR_QUEUE
from qdo.config import STATUS_PARTITIONS
from qdo.config import STATUS_QUEUE
from qdo.partition import Partition
from qdo.log import get_logger


@contextmanager
def dict_context():
    """The default job context manager. It sets context to be a dict.
    """
    context = dict()
    try:
        yield context
    finally:
        del context


def _log_raven():
    logger = get_logger()
    raven = getattr(logger, u'raven', None)
    if raven is not None:
        raven()


def log_failure(message, context, queue, exc, queuey_conn):
    """A simple job failure handler. It logs a full traceback for any failed
    job using `metlog-raven`.
    """
    _log_raven()


def save_failed_message(message, context, queue, exc, queuey_conn):
    """A job failure handler. It does the same as the `log_failure` handler
    and in addition saves a copy of each failed message in a special error
    queue named `qdo_error` in Queuey.

    Failed messages get a TTL of 30 days to provide some more time for
    debugging purposes. The failed messages are left in their original queues
    untouched, but will be purged after the shorter but configurable Queuey
    default TTL (3 days).
    """

    _log_raven()
    # record <queue>-<partition> of the failed message
    message[u'queue'] = queue
    try:
        queuey_conn.post(ERROR_QUEUE, data=ujson_encode(message),
            headers={u'X-TTL': u'2592000'})  # thirty days
    except Exception:  # pragma: no cover
        # never fail in the failure handler itself
        _log_raven()


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
        self.job = None
        self.job_context = dict_context
        self.job_failure = log_failure
        self.partition_policy = u'manual'
        self.partitions = {}
        self.queuey_conn = None
        self.zk_client = None
        self.zk_part = None
        self.configure()

    def configure(self):
        # Configure the worker based on the configuration settings.
        qdo_section = self.settings.getsection(u'qdo-worker')
        self.name = u'%s-%s' % (socket.getfqdn(), os.getpid())
        identifier = qdo_section[u'name']
        if identifier:
            self.name = self.name + u'-' + identifier
        self.wait_interval = qdo_section[u'wait_interval']
        resolve(self, qdo_section, u'job')
        resolve(self, qdo_section, u'job_context')
        resolve(self, qdo_section, u'job_failure')
        queuey_section = self.settings.getsection(u'queuey')
        self.queuey_conn = Client(
            queuey_section[u'app_key'],
            connection=queuey_section[u'connection'])
        zk_section = self.settings.getsection(u'zookeeper')
        self.zk_hosts = zk_section[u'connection']
        self.zk_party_wait = zk_section[u'party_wait']

    def setup_zookeeper(self):
        self.zk_client = KazooClient(hosts=self.zk_hosts, max_retries=1)
        self.zk_client.start()

    def _partitions(self):
        # List all partitions
        queuey_conn = self.queuey_conn
        response = queuey_conn.get(params={u'details': True})
        queues = ujson_decode(response.text)[u'queues']
        partitions = []
        for q in queues:
            name = q[u'queue_name']
            part = q[u'partitions']
            for i in xrange(1, part + 1):
                partitions.append(u'%s-%s' % (name, i))
        return partitions

    def configure_partitions(self, section):
        self.partition_policy = policy = section[u'policy']
        self.partition_ids = []
        queuey_conn = self.queuey_conn
        all_partitions = self._partitions()
        if policy == u'manual':
            self.partition_ids = section[u'ids']
        elif policy == u'all':
            self.partition_ids = all_partitions
        elif policy == u'automatic':
            self.setup_zookeeper()
            self.zk_part = self.zk_client.SetPartitioner(
                u'/worker', set=tuple(all_partitions), identifier=self.name,
                time_boundary=self.zk_party_wait)

            # XXX we don't want all partitions
            self.partition_ids = all_partitions

        def cond_create(queue_name):
            if queue_name + u'-1' not in all_partitions:
                queuey_conn.create_queue(
                    queue_name=queue_name, partitions=STATUS_PARTITIONS)
        cond_create(ERROR_QUEUE)
        cond_create(STATUS_QUEUE)
        self.status = self.status_partitions()

    def status_partitions(self):
        status = {}
        # get all status messages, starting with the newest ones
        status_messages = self.queuey_conn.messages(
            STATUS_QUEUE, limit=1000, order='descending')
        if len(status_messages) >= 1000:
            # TODO deal with more than 1000 status messages / partitions
            raise RuntimeError(u'More than 1000 status messages detected!')
        for message in status_messages:
            body = ujson_decode(message[u'body'])
            partition = body[u'partition']
            if partition not in status:
                # don't overwrite newer messages with older status
                status[partition] = message[u'message_id']
        return status

    def assign_partitions(self):
        partition_ids = self.partition_ids
        for pid in list(self.partitions.keys()):
            if pid not in partition_ids:
                del self.partitions[pid]
        status = self.status
        for pid in partition_ids:
            if pid.startswith((ERROR_QUEUE, STATUS_QUEUE)):
                continue
            self.partitions[pid] = Partition(self.queuey_conn, pid,
                msgid=status.get(pid, None), worker_id=self.name)

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
        self.assign_partitions()
        atexit.register(self.stop)
        timer = get_logger().timer
        zk_part = self.zk_part
        with self.job_context() as context:
            if zk_part is not None:
                if zk_part.allocating:
                    zk_part.wait_for_acquire(self.zk_party_wait)
            waited = 0
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
                    message_id = message[u'message_id']
                    try:
                        with timer(u'worker.job_time'):
                            self.job(message, context)
                    except Exception as exc:
                        with timer(u'worker.job_failure_time'):
                            self.job_failure(message, context,
                                name, exc, self.queuey_conn)
                    partition.last_message = message_id
                if no_messages == len(self.partitions):
                    self.wait(waited)
                    waited += 1
                else:
                    waited = 0

    def wait(self, waited=1):
        get_logger().incr(u'worker.wait_for_jobs')
        jitter = random.uniform(0.8, 1.2)
        time.sleep(self.wait_interval * jitter * 2 ** min(waited, 10))

    def stop(self):
        """Stop the worker loop. Used in an `atexit` hook."""
        if self.zk_client is not None:
            if self.zk_part is not None:
                self.zk_part.finish()
            self.zk_client.stop()
        self.shutdown = True


def run(settings):
    worker = Worker(settings)
    worker.work()
