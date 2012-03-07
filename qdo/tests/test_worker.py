# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time
import unittest

import ujson
from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import QdoSettings
from qdo.config import ZOO_DEFAULT_NS

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


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
        # clean up zookeeper
        if (self.worker.zkconn and
            self.worker.zkconn.handle is not None):

            self.worker.zkconn.close()
        # clean up queuey
        queuey_conn = self.worker.queuey_conn
        response = queuey_conn.get()
        queues = ujson.decode(response.text)[u'queues']
        names = [q[u'queue_name'] for q in queues]
        for n in names:
            queuey_conn.delete(n)
        del self.worker
        del self.queue_name

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = QdoSettings()
        settings['queuey.app_key'] = TEST_APP_KEY
        if extra is not None:
            settings.update(extra)
        self.worker = Worker(settings)
        self.queue_name = self.worker.queuey_conn._create_queue()
        return self.worker

    def _post_message(self, data):
        queuey_conn = self.worker.queuey_conn
        queuey_conn.post(self.queue_name, data=data)

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

    def test_work_no_job(self):
        worker = self._make_one()
        worker.work()
        # without a job, we should reach this and not loop
        self.assertTrue(True)

    def test_work_shutdown(self):
        worker = self._make_one()
        worker.shutdown = True
        worker.job = True
        worker.work()
        self.assertEqual(worker.shutdown, True)

    def test_work(self):
        worker = self._make_one()

        def stop(message):
            raise KeyboardInterrupt

        worker.job = stop
        self._post_message(u'Hello')
        self.assertRaises(KeyboardInterrupt, worker.work)

    def test_work_multiple(self):
        from qdo.utils import metlogger
        before = len(metlogger.sender.msgs)
        worker = self._make_one()
        # keep a runtime counter
        processed = [0]

        def stop(message, processed=processed):
            if processed[0] > 4:
                raise ValueError
            if message[u'body'] == u'end':
                raise KeyboardInterrupt
            # process the message
            processed[0] += 1
            return

        worker.job = stop
        self._post_message(u'work')
        self._post_message(u'work')
        self._post_message(u'work')
        time.sleep(0.02)
        self._post_message(u'work')
        self._post_message(u'end')

        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(processed[0], 4)
        log_messages = list(metlogger.sender.msgs)[before:]
        names = [ujson.decode(l)[u'fields'][u'name'] for l in log_messages]
        self.assertEqual(set(names),
            set([u'zookeeper.get_value', u'queuey.get_queues',
                 u'queuey.get_messages', u'zookeeper.set_value']))
