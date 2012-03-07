# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import time
import socket

import ujson
import zookeeper
from zc.zk import ZooKeeper
from zktools.locking import ZkWriteLock
from zktools.node import ZkNode

from qdo.queue import Queue
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
        self.zkconn = None
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

    def _get_queues(self):
        # Prototype for listing all queues
        response = self.queuey_conn.get(params={'details': True})
        queues = ujson.decode(response.text)[u'queues']
        queue_names = []
        for q in queues:
            name = q[u'queue_name']
            part = q[u'partitions']
            for i in xrange(1, part+1):
                queue_names.append(name + u'-%s' % i)
        return queue_names

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
        # track queues
        with metlogger.timer('queuey.get_queues'):
            queue_names = self._get_queues()
        self.zk_queue_nodes = zk_queue_nodes = []
        self.zk_queue_locks = zk_queue_locks = {}
        self.queues = queues = []
        for name in queue_names:
            node = ZkNode(self.zkconn, u'/queues/' + name, use_json=True)
            if node.value is None:
                node.value = 0.0
            zk_queue_nodes.append(node)
            zk_queue_locks[name] = ZkWriteLock(self.zkconn, name,
                lock_root=u'/queue-locks')
            queues.append(Queue(self.queuey_conn, name))

        try:
            while 1:
                if self.shutdown:
                    break
                no_messages = 0
                for num in xrange(len(queues)):
                    zk_queue_node = zk_queue_nodes[num]
                    queue = queues[num]
                    try:
                        with metlogger.timer('zookeeper.get_value'):
                            since = float(zk_queue_node.value)
                        with metlogger.timer('queuey.get_messages'):
                            data = queue.get(since=since, limit=2)
                        messages = data[u'messages']
                        message = messages[0]
                        timestamp = message[u'timestamp']
                        if timestamp == since:
                            # skip an exact match
                            message = messages[1]
                            timestamp = message[u'timestamp']
                        self.job(message)
                        with metlogger.timer('zookeeper.set_value'):
                            zk_queue_node.value = repr(timestamp)
                    except IndexError:
                        no_messages += 1
                if no_messages == len(queues):
                    metlogger.incr('worker.wait_for_jobs')
                    time.sleep(self.wait_interval)
        finally:
            self.unregister()

    def setup_zookeeper(self):
        """Setup global data structures in :term:`Zookeeper`."""
        self.zkconn = ZooKeeper(self.zk_root_url)
        ZkNode(self.zkconn, "/workers")
        ZkNode(self.zkconn, "/queues")
        ZkNode(self.zkconn, "/queue-locks")

    def register(self):
        """Register this worker with :term:`Zookeeper`."""
        self.zk_worker_node = ZkNode(self.zkconn, "/workers/" + self.name,
            create_mode=zookeeper.EPHEMERAL)

    def unregister(self):
        """Unregister this worker from :term:`Zookeeper`."""
        self.zkconn.close()


def run(settings):  # pragma: no cover
    worker = Worker(settings)
    worker.work()
