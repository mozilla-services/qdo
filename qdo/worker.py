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
        self.queue = Queue(queuey_conn, '1234')

    def work(self):
        """Work on jobs.

        This is the main method of the worker.
        """
        # Try Queuey heartbeat connection
        self.queuey_conn.connect()
        # Set up Zookeeper
        self.setup_zookeeper()
        self.register()
        # XXX: Save in Zookeper
        done = 0
        try:
            while 1:
                if self.shutdown:
                    break
                try:
                    messages = self.queue.get(since=done, limit=1)
                    message = messages[u'messages'][0]
                    timestamp = message[u'timestamp']
                    if self.job:
                        self.job(message)
                        done = timestamp
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
        self.zk_worker_node = ZkNode(self.zkconn, "/workers/%s" % self.name,
            create_mode=zookeeper.EPHEMERAL)

    def unregister(self):
        """Unregister this worker from :term:`Zookeeper`."""
        self.zkconn.close()


def run(settings):  # pragma: no cover
    worker = Worker(settings)
    worker.work()
