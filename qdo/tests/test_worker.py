# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import contextmanager
import time

import ujson
import unittest2 as unittest

from qdo.config import QdoSettings
from qdo import testing
from qdo.tests.base import BaseTestCase


class TestWorker(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        cls.zk_conn = cls._make_zk_conn()
        cls.supervisor = testing.processes[u'supervisor']

    @classmethod
    def tearDownClass(cls):
        cls.zk_conn.close()
        BaseTestCase.tearDownClass()

    def tearDown(self):
        if self.worker.zk_reactor is not None:
            self.worker.zk_reactor.close()

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = QdoSettings()
        settings[u'queuey.app_key'] = self.queuey_app_key
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
        children = worker.zk_reactor.get_children(u'/')
        self.assertTrue(u'workers' in children, children)
        self.assertTrue(u'partitions' in children, children)
        self.assertTrue(u'partition-owners' in children, children)

    def test_register(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_reactor.exists(u'/workers'))
        children = worker.zk_reactor.get_children(u'/workers')
        self.assertEqual(len(children), 1)

    def test_register_twice(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_reactor.exists(u'/workers'))
        children = worker.zk_reactor.get_children(u'/workers')
        self.assertEqual(len(children), 1)
        # a second call to register neither fails nor adds a duplicate
        worker.register()
        children = worker.zk_reactor.get_children(u'/workers')
        self.assertEqual(len(children), 1)

    def test_unregister(self):
        worker = self._make_one()
        worker.setup_zookeeper()
        worker.register()
        self.assertTrue(worker.zk_reactor.exists(u'/workers'))
        children = worker.zk_reactor.get_children(u'/workers')
        self.assertEqual(len(children), 1)
        self.assertEqual(children[0], worker.name)
        before_version = worker.zk_reactor.get(u'/workers')[1][u'cversion']
        worker.unregister()
        # wait for changes to propagate
        for i in xrange(0, 10):
            if (self.zk_conn.get(
                u'/workers')[1][u'cversion'] != before_version):
                break
            else:
                time.sleep(i * 0.1)
        self.assertEqual(self.zk_conn.get_children(u'/workers'), [])

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

        def job(context, message):
            raise KeyboardInterrupt

        worker.job = job
        self._post_message(u'Hello')
        self.assertRaises(KeyboardInterrupt, worker.work)

    def test_work_context(self):
        worker = self._make_one()
        context = {}

        @contextmanager
        def job_context(context=context):
            context[u'counter'] = 0
            context[u'done'] = False
            try:
                yield context
            finally:
                context[u'done'] = True

        def job(context, message):
            context[u'counter'] += 1
            if message[u'body'] == u'end':
                raise KeyboardInterrupt

        worker.job = job
        worker.job_context = job_context

        self._post_message(u'work')
        self._post_message(u'end')
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(context[u'counter'], 2)
        self.assertEqual(context[u'done'], True)

    def test_work_multiple_messages(self):
        worker = self._make_one()
        counter = [0]

        def job(context, message, counter=counter):
            counter[0] += 1
            if counter[0] > 5:
                raise ValueError
            if message[u'body'] == u'end':
                raise KeyboardInterrupt

        worker.job = job
        self._post_message(u'work')
        self._post_message(u'work')
        self._post_message(u'work')
        time.sleep(0.02)
        last = self._post_message(u'work')
        self._post_message(u'end')
        last_timestamp = float(str(ujson.decode(
            last.text)[u'messages'][0][u'timestamp']))

        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 5)
        self.assertEqual(
            self.worker.partitions.values()[0].timestamp, last_timestamp)

    def test_work_multiple_queues(self):
        worker = self._make_one()
        queue2 = self.worker.queuey_conn._create_queue()
        self._post_message(u'queue1-1')
        self._post_message(u'queue1-2')
        self._post_message(u'queue2-1', queue_name=queue2)
        self._post_message(u'queue2-2', queue_name=queue2)
        self._post_message(u'queue2-3', queue_name=queue2)
        counter = [0]

        def job(context, message, counter=counter):
            counter[0] += 1
            if counter[0] == 5:
                raise KeyboardInterrupt
            elif counter[0] > 5:
                raise ValueError

        worker.job = job
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 5)

    def test_work_multiple_empty_queues(self):
        worker = self._make_one()
        self.worker.queuey_conn._create_queue()
        self.worker.queuey_conn._create_queue()
        queue2 = self.worker.queuey_conn._create_queue()
        self._post_message(u'queue1-1')
        self._post_message(u'queue1-2')
        self._post_message(u'queue2-1', queue_name=queue2)
        counter = [0]

        def job(context, message, counter=counter):
            counter[0] += 1
            if counter[0] == 3:
                raise KeyboardInterrupt
            elif counter[0] > 3:
                raise ValueError

        worker.job = job
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 3)

    def test_work_multiple_queues_and_partitions(self):
        worker = self._make_one()
        queuey_conn = worker.queuey_conn
        queue2 = queuey_conn._create_queue(partitions=3)
        self._post_message([u'1', u'2'])
        # post messages to fill multiple partitions
        response = self._post_message(
            ['%s' % i for i in xrange(8)], queue_name=queue2)
        partitions = set([m[u'partition'] for m in
            ujson.decode(response.text)[u'messages']])
        # messages ended up in different partitions
        self.assertTrue(len(partitions) > 1, partitions)
        counter = [0]

        def job(context, message, counter=counter):
            counter[0] += 1
            if counter[0] == 10:
                raise KeyboardInterrupt
            elif counter[0] > 10:
                raise ValueError

        worker.job = job
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 10)

    def test_work_lost_zookeeper(self):
        worker = self._make_one()
        counter = [0]

        def job(context, message, counter=counter):
            counter[0] += 1
            body = message[u'body']
            if body == u'kill':
                # shut down the current zk server
                self.supervisor.stopProcess(u'zookeeper:zk1')
            elif body == u'end':
                raise KeyboardInterrupt

        worker.job = job
        self._post_message(u'work')
        self._post_message(u'kill')
        last = self._post_message(u'work')
        self._post_message(u'end')
        last_timestamp = float(ujson.decode(
            last.text)[u'messages'][0][u'timestamp'])
        try:
            self.assertRaises(KeyboardInterrupt, worker.work)
        finally:
            testing.ensure_process(u'zookeeper:zk1', noisy=False)
        self.assertEqual(counter[0], 4)
        self.assertEqual(
            self.worker.partitions.values()[0].timestamp, last_timestamp)


class TestRealWorker(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        cls.zk_conn = cls._make_zk_conn()
        cls.supervisor = testing.processes[u'supervisor']

    @classmethod
    def tearDownClass(cls):
        cls.zk_conn.close()
        BaseTestCase.tearDownClass()

    def test_work_real_process(self):
        zk_conn = self._zk_conn
        self._queuey_conn._create_queue(partitions=2)
        try:
            self.supervisor.startProcess(u'qdo:qdo1')
            time.sleep(0.1)
        finally:
            self.supervisor.stopProcess(u'qdo:qdo1')
        # worker has cleaned up after itself
        time.sleep(1.0)
        self.assertEqual(len(zk_conn.get_children(u'/workers')), 0)
        self.assertEqual(len(zk_conn.get_children(u'/partition-owners')), 0)

    # @unittest.expectedFailure
    def DISABLE_test_work_real_processes(self):
        return
        queuey_conn = self._queuey_conn
        zk_conn = self._zk_conn
        queue1 = queuey_conn._create_queue(partitions=1)
        queue2 = queuey_conn._create_queue(partitions=2)
        queue3 = queuey_conn._create_queue(partitions=3)
        data = [u'%s' % i for i in xrange(9)]
        for name in (queue1, queue2, queue3):
            queuey_conn.post(name, data=data)
        try:
            # start first worker
            testing.ensure_process(u'qdo:qdo1', noisy=False)
            self.assertEqual(len(zk_conn.get_children(u'/workers')), 1)
            # start second worker
            testing.ensure_process(u'qdo:qdo2', noisy=False)
            self.assertEqual(len(zk_conn.get_children(u'/workers')), 2)
            # start third worker
            testing.ensure_process(u'qdo:qdo3', noisy=False)
            self.assertEqual(len(zk_conn.get_children(u'/workers')), 3)
            # stop second worker
            self.supervisor.stopProcess(u'qdo:qdo2')
            time.sleep(0.1)
            # second worker has unregistered itself
            self.assertEqual(len(zk_conn.get_children(u'/workers')), 2)
            # check
            partitions = zk_conn.get_children(u'/partitions')
            self.assertEqual(len(partitions), 6)
            owners = {}
            for partition in partitions:
                # each partition was processed
                value = zk_conn.get(u'/partitions/' + partition)[0]
                self.assertNotEqual(value, u'0.0')
                # keep track of ownership
                owner = zk_conn.get(u'/partition-owners/' + partition)[0]
                if owner not in owners:
                    owners[owner] = [partition]
                else:
                    owners[owner].append(partition)
            # every worker did something
            self.assertEqual(len(owners), 2)
            for partitions in owners.values():
                self.assertTrue(len(partitions) > 0)
        finally:
            self.supervisor.stopProcessGroup(u'qdo')
