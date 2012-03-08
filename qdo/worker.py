# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import time
import socket

import zookeeper
from zc.zk import ZooKeeper
from zktools.locking import ZkWriteLock
from zktools.node import ZkNode

from qdo.partition import Partition
from qdo.queuey import QueueyConnection
from qdo.utils import metlogger


class Worker(object):
    """A Worker works on jobs.

    :param settings: Configuration settings
    :type settings: dict
    """

    def __init__(self, settings):
        self.settings = settings
        self.shutdown = False
        self.name = "%s-%s" % (socket.getfqdn(), os.getpid())
        self.zk_conn = None
        self.zk_worker_node = None
        self.configure()
        self.job = None

    def configure(self):
        """Configure the worker based on the configuration settings.
        """
        qdo_section = self.settings.getsection('qdo-worker')
        self.wait_interval = qdo_section['wait_interval']
        zk_section = self.settings.getsection('zookeeper')
        zkhost = zk_section['connection']
        zkns = zk_section['namespace']
        self.zk_root_url = zkhost + '/' + zkns
        queuey_section = self.settings.getsection('queuey')
        self.queuey_conn = QueueyConnection(
            queuey_section['app_key'],
            connection=queuey_section['connection'])

    def _get_workers(self):
        # Get all active worker names registered in ZK
        with metlogger.timer('zookeeper.get_workers'):
            return self.zk_conn.get_children(u'/workers')

    def _assign_partitions(self):
        # implement simplified Kafka re-balancing algorithm
        # 1. let this worker be Wi
        # 2. let P be all partitions
        partitions = self.queuey_conn._get_partitions()
        # 3. let W be all workers
        workers = self._get_workers()
        # 4. sort P
        partitions = sorted(partitions)
        # 5. sort W
        workers = sorted(workers)
        # 6. let i be the index position of Wi in W and
        #    let N = size(P) / size(W)
        i = workers.index(self.name)
        N = len(partitions) / len(workers)
        # 7. assign partitions from i*N to (i+1)*N - 1 to Wi
        local_partitions = []
        for num in xrange(i * N, (i + 1) * N):
            local_partitions.append(partitions[num])
        # 8. remove current entries owned by Wi from the partition owner registry
        # 9. add newly assigned partitions to the partition owner registry
        #    (we may need to re-try this until the original partition owner
        #     releases its ownership)
        return local_partitions

    def work(self):
        """Work on jobs.

        This is the main method of the worker.
        """
        if not self.job:
            return
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        # Set up Zookeeper
        self.setup_zookeeper()
        self.register()
        # track partitions
        new_partitions = self._assign_partitions()
        self.zk_partition_nodes = zk_partition_nodes = {}
        self.zk_partition_locks = zk_partition_locks = {}
        self.partitions = partitions = []
        for name in new_partitions:
            node = ZkNode(self.zk_conn, u'/partitions/' + name, use_json=True)
            if node.value is None:
                node.value = 0.0
            zk_partition_nodes[name] = node
            zk_partition_locks[name] = ZkWriteLock(self.zk_conn, name,
                lock_root=u'/partition-owners')
            partitions.append(Partition(self.queuey_conn, self.zk_conn, name))

        try:
            while 1:
                if self.shutdown:
                    break
                no_messages = 0
                for num in xrange(len(partitions)):
                    partition = partitions[num]
                    partition_name = partition.name
                    zk_partition_node = zk_partition_nodes[partition_name]
                    # zk_partition_lock = zk_partition_locks[partition_name]
                    try:
                        with metlogger.timer('zookeeper.get_value'):
                            since = float(zk_partition_node.value)
                        with metlogger.timer('queuey.get_messages'):
                            data = partition.get(since=since, limit=2)
                        messages = data[u'messages']
                        message = messages[0]
                        timestamp = message[u'timestamp']
                        if timestamp == since:
                            # skip an exact match
                            message = messages[1]
                            timestamp = message[u'timestamp']
                        self.job(message)
                        with metlogger.timer('zookeeper.set_value'):
                            zk_partition_node.value = repr(timestamp)
                    except IndexError:
                        no_messages += 1
                if no_messages == len(partitions):
                    metlogger.incr('worker.wait_for_jobs')
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
        self.zk_worker_node = ZkNode(self.zk_conn, u'/workers/' + self.name,
            create_mode=zookeeper.EPHEMERAL)
        # TODO: register a watch for /workers for changes
        # TODO: register a watch for /partitions for changes

    def unregister(self):
        """Unregister this worker from :term:`Zookeeper`."""
        self.zk_conn.close()


def run(settings):  # pragma: no cover
    worker = Worker(settings)
    worker.work()
