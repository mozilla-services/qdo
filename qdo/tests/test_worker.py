# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

from mozsvc.config import SettingsDict
from zc.zk import ZooKeeper
from zktools.node import ZkNode


class TestWorkerConfig(unittest.TestCase):

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = SettingsDict()
        if extra is not None:
            settings.update(extra)
        return Worker(settings)

    def test_configure(self):
        extra = {'qdo-worker.wait_interval': 30}
        worker = self._make_one(extra)
        self.assertEqual(worker.wait_interval, 30)

    def test_work_shutdown(self):
        worker = self._make_one()
        worker.shutdown = True
        worker.work()
        self.assertEqual(worker.shutdown, True)


class TestWorker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from qdo.worker import ZOO_DEFAULT_NS
        root = '/' + ZOO_DEFAULT_NS
        cls.zkconn = ZooKeeper('127.0.0.1:2181', wait=True)
        cls.zkconn.delete_recursive(root)
        ZkNode(cls.zkconn, root)
        cls.zkconn.close()
        cls.zkconn = ZooKeeper('127.0.0.1:2181' + root, wait=True)

    @classmethod
    def tearDownClass(cls):
        cls.zkconn.close()

    def setUp(self):
        for child in self.zkconn.get_children('/'):
            self.zkconn.delete_recursive('/' + child)

    def tearDown(self):
        if self.worker and self.worker.zkconn.handle is not None:
            self.worker.zkconn.close()

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = SettingsDict()
        if extra is not None:
            settings.update(extra)
        self.worker = Worker(settings)
        return self.worker

    def test_work(self):
        worker = self._make_one()
        worker.messages.append(json.dumps({'msgid': 1}))
        worker.messages.append(json.dumps({'msgid': 2}))

        def stop(message):
            raise KeyboardInterrupt

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(len(worker.messages), 1)

    def test_work_twice(self):
        worker = self._make_one()
        worker.messages.append(json.dumps({'msgid': 1}))
        worker.messages.append(json.dumps({'msgid': 2}))

        def stop(message):
            data = json.loads(message)
            if data['msgid'] == 1:
                # process the first message
                return
            raise KeyboardInterrupt

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(len(worker.messages), 0)

    def test_setup_zookeeper(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        self.assertTrue(worker.zkconn.exists('/workers'))

    def test_register(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zkconn.exists('/workers'))
        children = worker.zkconn.get_children('/workers')
        self.assertEqual(len(children), 1)

    def test_register_twice(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zkconn.exists('/workers'))
        children = worker.zkconn.get_children('/workers')
        self.assertEqual(len(children), 1)
        # a second call to register neither fails nor adds a duplicate
        worker.register()
        children = worker.zkconn.get_children('/workers')
        self.assertEqual(len(children), 1)

    def test_unregister(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zkconn.exists('/workers'))
        children = worker.zkconn.get_children('/workers')
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], worker.name)
        worker.unregister()
        self.assertTrue(worker.zkconn.handle is None)
        self.assertEqual(
            self.zkconn.get_children('/workers'), [])
