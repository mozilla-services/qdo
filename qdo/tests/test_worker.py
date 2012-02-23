# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

import mock
from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import QdoSettings
from qdo.config import ZOO_DEFAULT_NS


class TestWorker(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = '/' + ZOO_DEFAULT_NS
        cls.zkconn = ZooKeeper('127.0.0.1:2181', wait=True)
        if cls.zkconn.exists(root):
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
        if (self.worker and self.worker.zkconn and
            self.worker.zkconn.handle is not None):

            self.worker.zkconn.close()

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = QdoSettings()
        if extra is not None:
            settings.update(extra)
        self.worker = Worker(settings)

        def no_connect():
            # disable queuey connection
            pass
        self.worker.queuey_conn.connect = no_connect
        return self.worker

    def test_work(self):
        worker = self._make_one()

        def stop(message):
            raise KeyboardInterrupt

        worker.job = stop
        test_messages = json.dumps({u'msgid': 1, u'msgid': 2})
        with mock.patch('qdo.queuey.QueueyConnection.get') as get_mock:
            get_mock.return_value.text = unicode(test_messages, 'utf-8')
            get_mock.return_value.status_code = 200
            self.assertRaises(KeyboardInterrupt, worker.work)

    def test_work_twice(self):
        worker = self._make_one()

        def stop(message):
            data = json.loads(message)
            if data['msgid'] == 1:
                # process the first message
                return
            raise KeyboardInterrupt

        worker.job = stop
        test_messages = json.dumps({u'msgid': 1, u'msgid': 2})
        with mock.patch('qdo.queuey.QueueyConnection.get') as get_mock:
            get_mock.return_value.text = unicode(test_messages, 'utf-8')
            get_mock.return_value.status_code = 200
            self.assertRaises(KeyboardInterrupt, worker.work)

    def test_work_shutdown(self):
        worker = self._make_one()
        worker.shutdown = True
        worker.work()
        self.assertEqual(worker.shutdown, True)

    def test_setup_zookeeper(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        children = worker.zkconn.get_children('/')
        self.assertTrue('workers' in children, children)
        self.assertTrue('queues' in children, children)
        self.assertTrue('queue-locks' in children, children)

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
