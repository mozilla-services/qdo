# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import contextmanager
import threading
import time

import ujson
from kazoo.testing import KazooTestHarness

from qdo.config import ERROR_QUEUE
from qdo.config import QdoSettings
from qdo.config import STATUS_PARTITIONS
from qdo.config import STATUS_QUEUE
from qdo.tests.base import BaseTestCase


def _make_worker(app_key, extra=None):
    from qdo.worker import Worker
    settings = QdoSettings()
    settings[u'queuey.app_key'] = app_key
    settings[u'partitions.policy'] = u'all'
    if extra is not None:
        settings.update(extra)
    worker = Worker(settings)
    queue_name = worker.queuey_conn.create_queue()
    return worker, queue_name


class TestWorker(BaseTestCase):

    def _make_one(self, extra=None):
        return _make_worker(self.queuey_app_key, extra=extra)

    def _post_message(self, worker, queue_name, data):
        queuey_conn = worker.queuey_conn
        return queuey_conn.post(queue_name, data=data)

    def test_special_queues(self):
        worker, queue_name = self._make_one()
        worker.configure_partitions(dict(policy=u'all'))
        worker.assign_partitions()
        partitions = worker._partitions()
        self.assertTrue(ERROR_QUEUE + u'-1' in partitions)
        self.assertTrue(STATUS_QUEUE + u'-1' in partitions)
        self.assertEqual(worker.partitions.keys(), [queue_name + u'-1'])
        worker.configure_partitions(
            dict(policy=u'manual', ids=[queue_name + u'-2']))
        worker.assign_partitions()
        self.assertEqual(worker.partitions.keys(), [queue_name + u'-2'])

    def test_work_no_job(self):
        worker, queue_name = self._make_one()
        worker.work()
        # without a job, we should reach this and not loop
        self.assertTrue(True)

    def test_work_shutdown(self):
        worker, queue_name = self._make_one()
        worker.shutdown = True
        worker.job = True
        worker.work()
        self.assertEqual(worker.shutdown, True)

    def test_work(self):
        worker, queue_name = self._make_one()

        def job(message, context):
            raise KeyboardInterrupt

        worker.job = job
        self._post_message(worker, queue_name, u'Hello')
        self.assertRaises(KeyboardInterrupt, worker.work)

    def test_work_context(self):
        worker, queue_name = self._make_one()
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

        self._post_message(worker, queue_name, u'work')
        self._post_message(worker, queue_name, u'end')
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(context[u'counter'], 2)
        self.assertEqual(context[u'done'], True)

    def test_work_multiple_messages(self):
        worker, queue_name = self._make_one()
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] > 5:
                raise ValueError
            if message[u'body'] == u'end':
                raise KeyboardInterrupt

        worker.job = job
        self._post_message(worker, queue_name, u'work')
        self._post_message(worker, queue_name, u'work')
        self._post_message(worker, queue_name, u'work')
        time.sleep(0.02)
        last = self._post_message(worker, queue_name, u'work')
        self._post_message(worker, queue_name, u'end')
        last_message = ujson.decode(
            last.text)[u'messages'][0][u'key']

        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(counter[0], 5)
        value = worker.partitions.values()[0].last_message
        self.assertEqual(value, last_message)

    def test_work_multiple_queues(self):
        worker, queue_name = self._make_one()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, queue_name, u'queue1-1')
        self._post_message(worker, queue_name, u'queue1-2')
        self._post_message(worker, queue2, u'queue2-1')
        self._post_message(worker, queue2, u'queue2-2')
        self._post_message(worker, queue2, u'queue2-3')
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
        worker, queue_name = self._make_one()
        worker.queuey_conn.create_queue()
        worker.queuey_conn.create_queue()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, queue_name, u'queue1-1')
        self._post_message(worker, queue_name, u'queue1-2')
        self._post_message(worker, queue2, u'queue2-1')
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
        worker, queue_name = self._make_one()
        queuey_conn = worker.queuey_conn
        queue2 = queuey_conn.create_queue(partitions=3)
        self._post_message(worker, queue_name, [u'1', u'2'])
        # post messages to fill multiple partitions
        response = self._post_message(worker, queue2,
            ['%s' % i for i in xrange(8)])
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

    def test_job_failure_handler(self):
        worker, queue_name = self._make_one()
        context = {}

        @contextmanager
        def job_context(context=context):
            context[u'counter'] = 0
            context[u'errors'] = []
            yield context

        def job(message, context):
            context[u'counter'] += 1
            if context[u'counter'] == 1:
                raise ValueError(u'job failed')
            else:
                raise KeyboardInterrupt

        def job_failure(message, context, name, exc, queuey_conn):
            context[u'errors'].append(exc)

        worker.job = job
        worker.job_context = job_context
        worker.job_failure = job_failure
        self._post_message(worker, queue_name, u'Fail')
        self._post_message(worker, queue_name, u'Finish')
        self.assertRaises(KeyboardInterrupt, worker.work)
        errors = context[u'errors']
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], ValueError))
        self.assertEqual(errors[0].args, (u'job failed', ))

    def test_job_failure_save_handler(self):
        worker, queue_name = self._make_one(extra={
            u'qdo-worker.job_failure': u'qdo.worker:save_failed_message'})
        queue2 = worker.queuey_conn.create_queue(partitions=10)
        self._post_message(worker, queue_name, [u'-1', u'-2'])
        self._post_message(worker, queue2,
            ['%s' % i for i in xrange(20)])
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] <= 20:
                raise ValueError(u'job failed: %s' % counter[0])
            else:
                raise KeyboardInterrupt

        worker.job = job
        self.assertRaises(KeyboardInterrupt, worker.work)

        partition_spec = ','.join(
            [unicode(i + 1) for i in range(STATUS_PARTITIONS)])
        failed_messages = worker.queuey_conn.messages(
            ERROR_QUEUE, partition=partition_spec)
        self.assertEqual(len(failed_messages), 20)
        error_partitions = [m[u'partition'] for m in failed_messages]
        # multiple error partitions are used, 20 messages aren't enough to
        # guarantee all 7 partitions get randomly selected
        self.assertTrue(len(set(error_partitions)) > 3)
        failures = [ujson.decode(m[u'body']) for m in failed_messages]
        # the first 20 of 22 failures get saved, two random ones aren't
        # processed
        data = set([int(f[u'body']) for f in failures])
        possible = set(xrange(-2, 20))
        self.assertTrue(data.issubset(possible))

    def test_multiple_workers(self):
        queuey_conn = self._queuey_conn
        events = []
        queues = []
        threads = []
        workers = []

        def job(message, context):
            if message[u'body'] == u'stop':
                raise KeyboardInterrupt

        for i in range(3):
            queue = queuey_conn.create_queue()
            queues.append(queue)
            worker, _ = self._make_one(extra={
                u'qdo-worker.name': u'worker%s' % i,
                u'partitions.policy': u'manual',
                u'partitions.ids': [queue + u'-1'],
                })
            worker.job = job
            workers.append(worker)

            self._post_message(worker, queue,
                [u'%s' % i for i in xrange(11)])
            self._post_message(worker, queue, u'stop')

            event = threading.Event()
            events.append(event)

            def run(event):
                try:
                    worker.work()
                except KeyboardInterrupt:
                    pass
                event.set()

            thread = threading.Thread(target=run, args=(event, ))
            thread.start()
            threads.append(thread)

        for i in range(3):
            events[i].wait()
            processed = workers[i].partitions.values()[0].last_message
            msgs = queuey_conn.messages(queues[i])
            self.assertEqual(msgs[-2]['message_id'], processed)


class TestKazooWorker(BaseTestCase, KazooTestHarness):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.setup_zookeeper()

    def tearDown(self):
        self.teardown_zookeeper()
        BaseTestCase.tearDown(self)

    def _make_one(self, extra=None):
        extra = {} if not extra else extra
        extra[u'zookeeper.connection'] = self.hosts
        extra[u'zookeeper.party_wait'] = 0.1
        return _make_worker(self.queuey_app_key, extra=extra)

    def _post_message(self, worker, queue_name, data):
        queuey_conn = worker.queuey_conn
        return queuey_conn.post(queue_name, data=data)

    def test_work(self):
        worker, queue_name = self._make_one(extra={
            u'partitions.policy': u'automatic'})
        counter = [0]

        def job(message, context):
            counter[0] += 1
            if counter[0] > 1:
                raise KeyboardInterrupt

        worker.job = job
        self._post_message(worker, queue_name, [u'1', u'2'])
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual([queue_name + u'-1'], list(worker.zk_part))
