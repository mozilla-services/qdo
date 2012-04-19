# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
from contextlib import contextmanager
import os
import time
import socket

from twisted.internet.defer import inlineCallbacks
import zookeeper

from qdo.partition import Partition
from qdo.queuey import QueueyConnection
from qdo.log import get_logger
from qdo import zk


@contextmanager
def dict_context():
    context = dict()
    try:
        yield context
    finally:
        del context


class Worker(object):
    """A Worker works on jobs.

    :param settings: Configuration settings
    :type settings: dict
    """

    def __init__(self, settings):
        self.settings = settings
        self.shutdown = False
        self.name = u'%s-%s' % (socket.getfqdn(), os.getpid())
        self.zk_reactor = None
        self.job = None
        self.job_context = dict_context
        self.partitions = {}
        self.configure()

    def configure(self):
        """Configure the worker based on the configuration settings.
        """
        qdo_section = self.settings.getsection(u'qdo-worker')
        self.wait_interval = qdo_section[u'wait_interval']
        if qdo_section[u'job']:
            mod, fun = qdo_section[u'job'].split(u':')
            result = __import__(mod, globals(), locals(), fun)
            self.job = getattr(result, fun)
        if qdo_section[u'job_context']:
            mod, fun = qdo_section[u'job_context'].split(u':')
            result = __import__(mod, globals(), locals(), fun)
            self.job_context = getattr(result, fun)
        zk_section = self.settings.getsection(u'zookeeper')
        self.zk_root_url = zk_section[u'connection']
        queuey_section = self.settings.getsection(u'queuey')
        self.queuey_conn = QueueyConnection(
            queuey_section[u'app_key'],
            connection=queuey_section[u'connection'])

    def _assign_partitions(self, worker_children):
        # implement simplified Kafka re-balancing algorithm
        # 1. let this worker be Wi
        # 2. let P be all partitions
        all_partitions = self.queuey_conn._partitions()
        # 3. let W be all workers
        workers = worker_children
        # 4. sort P
        all_partitions = sorted(all_partitions)
        # 5. sort W
        workers = sorted(workers)
        # 6. let i be the index position of Wi in W and
        #    let N = size(P) / size(W)
        i = workers.index(self.name)
        N = len(all_partitions) / len(workers)
        # 7. assign partitions from i*N to (i+1)*N - 1 to Wi
        new_partitions = set()
        for num in xrange(i * N, (i + 1) * N):
            new_partitions.add(all_partitions[num])
        # 8. remove current entries owned by Wi from the partition owner
        # registry
        old_partitions = set(self.partitions.keys())
        for name in old_partitions - new_partitions:
            del self.partitions[name]
            # TODO: wrong, needs to be a lock
            self.zk_conn.delete(u'/partition-owners/' + name)
        # 9. add newly assigned partitions to the partition owner registry
        #    (we may need to re-try this until the original partition owner
        #     releases its ownership)
        for name in new_partitions - old_partitions:
            self.partitions[name] = Partition(
                self.queuey_conn, self.zk_reactor, name)
            # TODO: wrong, needs to be a lock
            zk_lock = u'/partition-owners/' + name
            zk.create(self.zk_conn, zk_lock, create_mode=zookeeper.EPHEMERAL)
            self.zk_conn.set(zk_lock, self.name)

    def work(self):
        """Work on jobs.

        This is the main loop of the worker.
        """
        if not self.job:
            return
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        # Set up Zookeeper
        self.setup_zookeeper()
        self.register()
        atexit.register(self.stop)
        try:
            with self.job_context() as context:
                while 1:
                    if self.shutdown:
                        break
                    # don't process anything while we re-assign partitions
                    # XXX self._worker_event.wait()
                    no_messages = 0
                    for name, partition in self.partitions.items():
                        messages = partition.messages(limit=2)
                        if not messages:
                            no_messages += 1
                            continue
                        message = messages[0]
                        timestamp = message[u'timestamp']
                        self.job(context, message)
                        partition.timestamp = timestamp
                    if no_messages == len(self.partitions):
                        get_logger().incr(u'worker.wait_for_jobs')
                        time.sleep(self.wait_interval)
        finally:
            self.unregister()

    def setup_zookeeper(self):
        """Setup global data structures in :term:`Zookeeper`."""
        self.zk_reactor = zk.ZKReactor(self.zk_root_url)
        self.zk_reactor.start()

    def register(self):
        """Register this worker with :term:`Zookeeper`."""
        self.zk_reactor.blocking_call(self._register)

    @inlineCallbacks
    def _register(self):
        # register a watch for /workers for changes
        # XXX self._worker_event = we = threading.Event()
        yield self.zk_reactor._create(u'/workers/' + self.name,
            flags=zookeeper.EPHEMERAL)

        children = yield self.zk_reactor.client.get_children(u'/workers')
        # self._assign_partitions(children)

        # XXX @self.zk_conn.children(u'/workers')
        # def workers_watcher(children):
        #     we.clear()
        #     with get_logger().timer(u'worker.assign_partitions'):
        #         self._assign_partitions(children.data)
        #     we.set()

        # We hold a reference to our function to ensure it is still
        # tracked since the decorator above uses a weak-ref
        # XXX self._workers_watcher = workers_watcher
        # we.wait()

        # TODO: register a watch for /partitions for changes

    def unregister(self):
        """Unregister this worker from :term:`Zookeeper`."""
        self.zk_reactor.close()

    def stop(self):
        """Stop the worker loop and unregister. Used in an `atexit` hook."""
        self.shutdown = True
        if self.zk_reactor is not None:
            self.zk_reactor.stop()


def run(settings):
    worker = Worker(settings)
    worker.work()
