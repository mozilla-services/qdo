# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import contextmanager
import time

import ujson

from qdo.config import ERROR_QUEUE
from qdo.config import QdoSettings
from qdo.config import STATUS_PARTITIONS
from qdo.config import STATUS_QUEUE
from qdo import testing
from qdo.tests.base import BaseTestCase


class TestWorker(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        if testing.SUPERVISOR:
            cls.supervisor = testing.processes[u'supervisor']

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = QdoSettings()
        settings[u'queuey.app_key'] = self.queuey_app_key
        if extra is not None:
            settings.update(extra)
        worker = Worker(settings)
        self.queue_name = worker.queuey_conn.create_queue()
        worker.settings[u'partitions.policy'] = u'all'
        return worker

    def _post_message(self, worker, data, queue_name=None):
        queuey_conn = worker.queuey_conn
        return queuey_conn.post(
            queue_name and queue_name or self.queue_name, data=data)

    def test_special_queues(self):
        worker = self._make_one()
        worker.configure_partitions(dict(policy=u'all'))
        partitions = worker._partitions()
        self.assertTrue(ERROR_QUEUE + u'-1' in partitions)
        self.assertTrue(STATUS_QUEUE + u'-1' in partitions)
        self.assertEqual(worker.partitions.keys(),
            [self.queue_name + u'-1'])
        worker.configure_partitions(
            dict(policy=u'manual', ids=[self.queue_name + u'-2']))
        self.assertEqual(worker.partitions.keys(),
            [self.queue_name + u'-2'])

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

        def job(message, context):
            raise KeyboardInterrupt

        worker.job = job
        self._post_message(worker, u'Hello')
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

        def job(message, context):
            context[u'counter'] += 1
            if message[u'body'] == u'end':
                raise KeyboardInterrupt

        worker.job = job
        worker.job_context = job_context

        self._post_message(worker, u'work')
        self._post_message(worker, u'end')
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(context[u'counter'], 2)
        self.assertEqual(context[u'done'], True)

    def test_work_multiple_messages(self):
        worker = self._make_one()
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] > 5:
                raise ValueError
            if message[u'body'] == u'end':
                raise KeyboardInterrupt

        worker.job = job
        self._post_message(worker, u'work')
        self._post_message(worker, u'work')
        self._post_message(worker, u'work')
        time.sleep(0.02)
        last = self._post_message(worker, u'work')
        self._post_message(worker, u'end')
        last_message = ujson.decode(
            last.text)[u'messages'][0][u'key']

        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 5)
        value = worker.partitions.values()[0].last_message
        self.assertEqual(value, last_message)

    def test_work_multiple_queues(self):
        worker = self._make_one()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, u'queue1-1')
        self._post_message(worker, u'queue1-2')
        self._post_message(worker, u'queue2-1', queue_name=queue2)
        self._post_message(worker, u'queue2-2', queue_name=queue2)
        self._post_message(worker, u'queue2-3', queue_name=queue2)
        counter = [0]

        def job(message, context, counter=counter):
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
        worker.queuey_conn.create_queue()
        worker.queuey_conn.create_queue()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, u'queue1-1')
        self._post_message(worker, u'queue1-2')
        self._post_message(worker, u'queue2-1', queue_name=queue2)
        counter = [0]

        def job(message, context, counter=counter):
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
        queue2 = queuey_conn.create_queue(partitions=3)
        self._post_message(worker, [u'1', u'2'])
        # post messages to fill multiple partitions
        response = self._post_message(worker,
            ['%s' % i for i in xrange(8)], queue_name=queue2)
        partitions = set([m[u'partition'] for m in
            ujson.decode(response.text)[u'messages']])
        # messages ended up in different partitions
        self.assertTrue(len(partitions) > 1, partitions)
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] == 10:
                raise KeyboardInterrupt
            elif counter[0] > 10:
                raise ValueError

        worker.job = job
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 10)


class TestRealWorker(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        BaseTestCase.setUpClass()
        cls.supervisor = testing.processes[u'supervisor']

    def test_work_real_process(self):
        self._queuey_conn.create_queue(partitions=2)
        try:
            self.supervisor.startProcess(u'qdo:qdo1')
            time.sleep(0.5)
        finally:
            self.supervisor.stopProcess(u'qdo:qdo1')

    def test_work_real_processes(self):
        queuey_conn = self._queuey_conn
        queue1 = queuey_conn.create_queue(partitions=1)
        queue2 = queuey_conn.create_queue(partitions=2)
        queue3 = queuey_conn.create_queue(partitions=3)
        data = [u'%s' % i for i in xrange(9)]
        for name in (queue1, queue2, queue3):
            queuey_conn.post(name, data=data)
        try:
            # start workers
            testing.ensure_process(u'qdo:qdo1', noisy=False)
            testing.ensure_process(u'qdo:qdo2', noisy=False)
            testing.ensure_process(u'qdo:qdo3', noisy=False)
            # stop second worker
            self.supervisor.stopProcess(u'qdo:qdo2')
            partition_spec = ','.join(
                [unicode(i + 1) for i in range(STATUS_PARTITIONS)])
            status_messages = queuey_conn.messages(
                STATUS_QUEUE, partition=partition_spec, order=u'descending')
            partitions = set([ujson.decode(sm[u'body'])[u'partition']
                for sm in status_messages])
            expected = set([queue1 + u'-1', queue2 + u'-1', queue2 + u'-2',
                queue3 + u'-1', queue3 + u'-2', queue3 + u'-3'])
            self.assertEqual(expected, partitions)
        finally:
            self.supervisor.stopProcessGroup(u'qdo')
