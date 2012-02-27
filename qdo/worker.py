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
        self.queuey_conn = queuey_conn = QueueyConnection(
            queuey_section['app_key'],
            server_url=queuey_section['url'])
        # XXX: define a real queue name
        self.queue_name = '1234'
        self.queue = Queue(queuey_conn, self.queue_name)

    def work(self):
        """Work on jobs.

        This is the main method of the worker.
        """
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        # Set up Zookeeper
        self.setup_zookeeper()
        self.register()
        # track queues
        zk_queue_node = ZkNode(self.zkconn, "/queues/" + self.queue_name,
            use_json=True)
        if zk_queue_node.value is None:
            zk_queue_node.value = 0.0
        try:
            while 1:
                if self.shutdown:
                    break
                try:
                    since = float(zk_queue_node.value)
                    messages = self.queue.get(since=since, limit=1)
                    message = messages[u'messages'][0]
                    timestamp = message[u'timestamp']
                    if self.job:
                        self.job(message)
                        zk_queue_node.value = repr(timestamp)
                        # XXX if the job finishes too fast, our ZK node
                        # hasn't been updated yet. Ideally we'd like to wait
                        # for our local zk node value to get updated
                        time.sleep(0.1)
                except IndexError:
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
