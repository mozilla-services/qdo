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
        cls.zk_conn = ZooKeeper('127.0.0.1:2181', wait=True)
        if cls.zk_conn.exists(root):
            cls.zk_conn.delete_recursive(root)
        ZkNode(cls.zk_conn, root)
        cls.zk_conn.close()
        cls.zk_conn = ZooKeeper('127.0.0.1:2181' + root, wait=True)

    @classmethod
    def tearDownClass(cls):
        cls.zk_conn.close()

    def setUp(self):
        for child in self.zk_conn.get_children('/'):
            self.zk_conn.delete_recursive('/' + child)

    def tearDown(self):
        # clean up zookeeper
        if (self.worker.zk_conn and
            self.worker.zk_conn.handle is not None):

            self.worker.zk_conn.close()
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

    def _post_message(self, data, queue_name=None):
        queuey_conn = self.worker.queuey_conn
        return queuey_conn.post(
            queue_name and queue_name or self.queue_name, data=data)

    def test_setup_zookeeper(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        children = worker.zk_conn.get_children('/')
        self.assertTrue('workers' in children, children)
        self.assertTrue('partitions' in children, children)
        self.assertTrue('partition-owners' in children, children)

    def test_register(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_conn.exists('/workers'))
        children = worker.zk_conn.get_children('/workers')
        self.assertEqual(len(children), 1)

    def test_register_twice(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_conn.exists('/workers'))
        children = worker.zk_conn.get_children('/workers')
        self.assertEqual(len(children), 1)
        # a second call to register neither fails nor adds a duplicate
        worker.register()
        children = worker.zk_conn.get_children('/workers')
        self.assertEqual(len(children), 1)

    def test_unregister(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_conn.exists('/workers'))
        children = worker.zk_conn.get_children('/workers')
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], worker.name)
        worker.unregister()
        self.assertTrue(worker.zk_conn.handle is None)
        self.assertEqual(
            self.zk_conn.get_children('/workers'), [])

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

    def test_work_multiple_messages(self):
        worker = self._make_one()
        # keep a runtime counter
        processed = [0]

        def stop(message, processed=processed):
            # process the message
            processed[0] += 1
            if processed[0] > 5:
                raise ValueError
            if message[u'body'] == u'end':
                raise KeyboardInterrupt
            return

        worker.job = stop
        self._post_message(u'work')
        self._post_message(u'work')
        self._post_message(u'work')
        time.sleep(0.02)
        self._post_message(u'work')
        self._post_message(u'end')

        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(processed[0], 5)

    def test_work_multiple_queues(self):
        worker = self._make_one()
        queue2 = self.worker.queuey_conn._create_queue()
        self._post_message(u'queue1-1')
        self._post_message(u'queue1-2')
        self._post_message(u'queue2-1', queue_name=queue2)
        self._post_message(u'queue2-2', queue_name=queue2)
        self._post_message(u'queue2-3', queue_name=queue2)
        processed = [0]

        def stop(message, processed=processed):
            # process the message
            processed[0] += 1
            if processed[0] == 5:
                raise KeyboardInterrupt
            elif processed[0] > 5:
                raise ValueError
            return

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(processed[0], 5)

    def test_work_multiple_empty_queues(self):
        worker = self._make_one()
        self.worker.queuey_conn._create_queue()
        self.worker.queuey_conn._create_queue()
        queue2 = self.worker.queuey_conn._create_queue()
        self._post_message(u'queue1-1')
        self._post_message(u'queue1-2')
        self._post_message(u'queue2-1', queue_name=queue2)
        processed = [0]

        def stop(message, processed=processed):
            # process the message
            processed[0] += 1
            if processed[0] == 3:
                raise KeyboardInterrupt
            elif processed[0] > 3:
                raise ValueError
            return

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(processed[0], 3)

    def test_work_multiple_queues_and_partitions(self):
        worker = self._make_one()
        queuey_conn = worker.queuey_conn
        queue2 = queuey_conn._create_queue(partitions=3)
        self._post_message(['1', '2'])
        # post messages to fill multiple partitions
        response = self._post_message(
            ['%s' % i for i in xrange(8)], queue_name=queue2)
        partitions = set([m[u'partition'] for m in
            ujson.decode(response.text)[u'messages']])
        # messages ended up in different partitions
        self.assertTrue(len(partitions) > 1, partitions)
        processed = [0]

        def stop(message, processed=processed):
            # process the message
            processed[0] += 1
            if processed[0] == 10:
                raise KeyboardInterrupt
            elif processed[0] > 10:
                raise ValueError
            return

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(processed[0], 10)
