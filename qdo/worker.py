# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import deque
import time

import zookeeper
from zktools.connection import ZkConnection

from qdo.utils import metlogger

ZOO_EPHEMERAL_AND_SEQUENCE = zookeeper.EPHEMERAL | zookeeper.SEQUENCE
ZOO_OPEN_ACL_UNSAFE = {"perms": 0x1f, "scheme": "world", "id": "anyone"}


class Worker(object):
    """A Worker works on jobs"""

    def __init__(self, settings):
        """Create a worker

        :param settings: Configuration settings
        :type settings: dict
        """
        self.settings = settings
        self.shutdown = False
        self.configure()
        self.messages = deque()
        self.job = None

    def configure(self):
        """Configure the worker based on the configuration settings.
        """
        qdo_section = self.settings.getsection('qdo-worker')
        self.wait_interval = qdo_section.get('wait_interval', 5)
        zkhost = qdo_section.get('zookeeper_connection', 'localhost:2181')
        self.zkconn = ZkConnection(host=zkhost, use_json=True)

    def work(self):
        """Work on jobs

        This is the main method of the worker.
        """
        self.register()
        try:
            while True:
                if self.shutdown:
                    break
                try:
                    message = self.messages.popleft()
                    if self.job:
                        self.job(message)
                except IndexError:
                    metlogger.incr('wait_for_jobs')
                    time.sleep(self.wait_interval)
        finally:
            self.unregister()

    def register(self):
        """Register this worker with Zookeeper."""
        self.zkconn.connect()
        try:
            self.zkconn.create("/workers", "",
                [ZOO_OPEN_ACL_UNSAFE], 0)
        except zookeeper.NodeExistsException:
            pass
        self.zkconn.create(
            "/workers/worker-", "value",
            [ZOO_OPEN_ACL_UNSAFE], ZOO_EPHEMERAL_AND_SEQUENCE)

    def unregister(self):
        """Unregister this worker from Zookeeper."""
        self.zkconn.close()


def run(settings):  # pragma: no cover
    worker = Worker(settings)
    worker.work()
