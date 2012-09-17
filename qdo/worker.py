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
    """Log exceptions using metlog-raven if it's configured."""
    logger = get_logger()
    raven = getattr(logger, 'raven', None)
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
    message['queue'] = queue
    try:
        queuey_conn.post(ERROR_QUEUE, data=ujson_encode(message),
            headers={'X-TTL': '2592000'})  # thirty days
    except Exception:  # pragma: no cover
        # never fail in the failure handler itself
        _log_raven()


def resolve(worker, section, name):
    # resolve a resource specification and set it onto the worker
    if section[name]:
        mod, func_name = section[name].split(':')
        result = __import__(mod, globals(), locals(), func_name)
        func = getattr(result, func_name)
        setattr(worker, name, func)


class StopWorker(Exception):
    """An exception which causes the worker loop to shut down cleanly.
    Especially useful in writing tests.
    """


class StaticPartitioner(object):
    """A partitioner using a static set list. Basic API compatibility
    with the `kazoo.recipe.SetPartitioner` is preserved.
    """

    failed = False
    release = False
    allocating = True
    acquired = False

    def __init__(self, path, set, identifier=None, time_boundary=0):
        # path and time_boundary are ignored and only here for API
        # compatibility with the kazoo version
        self._set = set
        self._identifier = identifier

    def __iter__(self):
        for s in self._set:
            yield s

    def wait_for_acquire(self, timeout=0):
        self.allocating = False
        self.acquired = True

    def release_set(self):  # pragma: no cover
        pass

    def finish(self):
        self.acquired = False
        self.failed = True


class PartitionCache(dict):

    def __init__(self, worker):
        self._worker = worker

    def __missing__(self, key):
        worker = self._worker
        self[key] = partition = Partition(worker.queuey_conn, key,
            msgid=worker.status.get(key, None), worker_id=worker.name)
        return partition


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
        self.partition_policy = 'manual'
        self.queuey_conn = None
        self.zk = None
        self.partitioner = None
        self.partition_cache = PartitionCache(self)
        self.configure()

    def configure(self):
        # Configure the worker based on the configuration settings.
        qdo_section = self.settings.getsection('qdo-worker')
        self.name = '%s-%s' % (socket.getfqdn(), os.getpid())
        identifier = qdo_section['name']
        if identifier:
            self.name += '-' + identifier
        self.wait_interval = qdo_section['wait_interval']
        resolve(self, qdo_section, 'job')
        resolve(self, qdo_section, 'job_context')
        resolve(self, qdo_section, 'job_failure')
        queuey_section = self.settings.getsection('queuey')
        self.queuey_conn = Client(
            queuey_section['app_key'],
            connection=queuey_section['connection'])
        zk_section = self.settings.getsection('zookeeper')
        self.zk_hosts = zk_section['connection']
        self.zk_party_wait = zk_section['party_wait']

    def setup_zookeeper(self):
        self.zk = KazooClient(hosts=self.zk_hosts, max_retries=1)
        self.zk.start()

    def all_partitions(self):
        # List all partitions
        queuey_conn = self.queuey_conn
        response = queuey_conn.get(params={'details': True})
        queues = ujson_decode(response.text)['queues']
        partitions = []
        for q in queues:
            name = q['queue_name']
            part = q['partitions']
            for i in xrange(1, part + 1):
                partitions.append('%s-%s' % (name, i))
        return partitions

    def configure_partitions(self):
        section = self.settings.getsection('partitions')
        self.partition_policy = policy = section['policy']
        queuey_conn = self.queuey_conn
        all_partitions = self.all_partitions()
        partition_ids = section.get('ids')
        partitioner_class = StaticPartitioner
        if not partition_ids:
            partition_ids = all_partitions
        if policy == 'automatic':
            self.setup_zookeeper()
            partitioner_class = self.zk.SetPartitioner

        partition_ids = [p for p in partition_ids if not
            p.startswith((ERROR_QUEUE, STATUS_QUEUE))]

        self.partitioner = partitioner_class(
            '/worker', set=tuple(partition_ids), identifier=self.name,
            time_boundary=self.zk_party_wait)

        def cond_create(queue_name):
            if queue_name + '-1' not in all_partitions:
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
        if len(status_messages) >= 1000:  # pragma: no cover
            # TODO deal with more than 1000 status messages / partitions
            raise RuntimeError('More than 1000 status messages detected!')
        for message in status_messages:
            body = ujson_decode(message['body'])
            partition = body['partition']
            if partition not in status:
                # don't overwrite newer messages with older status
                status[partition] = message['message_id']
        return status

    def work(self):
        """Work on jobs."""
        if not self.job:
            return
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        self.configure_partitions()
        atexit.register(self.stop)
        timer = get_logger().timer
        partitioner = self.partitioner
        with self.job_context() as context:
            if partitioner.allocating:
                partitioner.wait_for_acquire(self.zk_party_wait)
            waited = 0
            while 1:
                if self.shutdown or partitioner.failed:
                    break
                if partitioner.release:
                    partitioner.release_set()
                elif partitioner.allocating:
                    partitioner.wait_for_acquire(self.zk_party_wait)
                elif partitioner.acquired:
                    no_messages = 0
                    partitions = list(self.partitioner)
                    for name in partitions:
                        partition = self.partition_cache[name]
                        messages = partition.messages(limit=2)
                        if not messages:
                            no_messages += 1
                            continue
                        message = messages[0]
                        message_id = message['message_id']
                        try:
                            with timer('worker.job_time'):
                                self.job(message, context)
                        except StopWorker:
                            self.shutdown = True
                            break
                        except Exception as exc:
                            with timer('worker.job_failure_time'):
                                self.job_failure(message, context,
                                    name, exc, self.queuey_conn)
                        # record successful message processing
                        partition.last_message = message_id
                    if no_messages == len(partitions):
                        # if none of the partitions had a message, wait
                        self.wait(waited)
                        waited += 1
                    else:
                        waited = 0
            # give up the partitions and leave party
            self.partitioner.finish()

    def wait(self, waited=1):
        get_logger().incr('worker.wait_for_jobs')
        jitter = random.uniform(0.8, 1.2)
        time.sleep(self.wait_interval * jitter * 2 ** min(waited, 10))

    def stop(self):
        """Stop the worker loop. Used in an `atexit` hook."""
        self.shutdown = True
        if self.zk is not None:
            self.partitioner.finish()
            self.zk.stop()


def run(settings):  # pragma: no cover
    worker = Worker(settings)
    worker.work()
