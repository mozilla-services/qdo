# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import time
import socket

import zookeeper
from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.partition import Partition
from qdo.queuey import QueueyConnection
from qdo.log import get_logger


class Worker(object):
    """A Worker works on jobs.

    :param settings: Configuration settings
    :type settings: dict
    """

    def __init__(self, settings):
        self.settings = settings
        self.shutdown = False
        self.name = u'%s-%s' % (socket.getfqdn(), os.getpid())
        self.zk_conn = None
        self.zk_node = None
        self.job = None
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
        zk_section = self.settings.getsection(u'zookeeper')
        self.zk_root_url = zk_section[u'connection'] + u'/' + \
            zk_section[u'namespace']
        queuey_section = self.settings.getsection(u'queuey')
        self.queuey_conn = QueueyConnection(
            queuey_section[u'app_key'],
            connection=queuey_section[u'connection'])

    def _workers(self):
        # Get all active worker names registered in ZK
        with get_logger().timer(u'zookeeper.get_workers'):
            return self.zk_conn.get_children(u'/workers')

    def _assign_partitions(self):
        # implement simplified Kafka re-balancing algorithm
        # 1. let this worker be Wi
        # 2. let P be all partitions
        all_partitions = self.queuey_conn._partitions()
        # 3. let W be all workers
        workers = self._workers()
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
        # 8. remove current entries owned by Wi from the partition owner registry
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
                self.queuey_conn, self.zk_conn, name)
            # TODO: wrong, needs to be a lock
            zk_lock = ZkNode(self.zk_conn, u'/partition-owners/' + name)
            zk_lock.value = self.name

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
        # track partitions
        self._assign_partitions()
        try:
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
                    self.job(message)
                    partition.timestamp = timestamp
                if no_messages == len(self.partitions):
                    get_logger().incr(u'worker.wait_for_jobs')
                    time.sleep(self.wait_interval)
        finally:
            self.unregister()

    def setup_zookeeper(self):
        """Setup global data structures in :term:`Zookeeper`."""
        self.zk_conn = ZooKeeper(self.zk_root_url)
        ZkNode(self.zk_conn, u'/workers')
        ZkNode(self.zk_conn, u'/partitions')
        ZkNode(self.zk_conn, u'/partition-owners')

    def register(self):
        """Register this worker with :term:`Zookeeper`."""
        self.zk_node = ZkNode(self.zk_conn, u'/workers/' + self.name,
            create_mode=zookeeper.EPHEMERAL)
        # TODO: register a watch for /workers for changes
        # TODO: register a watch for /partitions for changes

    def unregister(self):
        """Unregister this worker from :term:`Zookeeper`."""
        self.zk_conn.close()


def run(settings):
    worker = Worker(settings)
    worker.work()
