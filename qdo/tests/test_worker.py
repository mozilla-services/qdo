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
from qdo.worker import StopWorker
from qdo.tests.base import BaseTestCase


def _make_worker(app_key, extra=None, queue=True):
    from qdo.worker import Worker
    settings = QdoSettings()
    settings['queuey.app_key'] = app_key
    if extra is not None:
        settings.update(extra)
    worker = Worker(settings)
    if queue:
        queue_name = worker.queuey_conn.create_queue()
    else:
        queue_name = None
    return worker, queue_name


class TestWorker(BaseTestCase):

    def _make_one(self, extra=None):
        return _make_worker(self.queuey_app_key, extra=extra)

    def _post_message(self, worker, queue_name, data):
        queuey_conn = worker.queuey_conn
        return queuey_conn.post(queue_name, data=data)

    def test_special_queues(self):
        worker, queue_name = self._make_one()
        worker.configure_partitions()
        partitions = worker.all_partitions()
        self.assertTrue(ERROR_QUEUE + '-1' in partitions)
        self.assertTrue(STATUS_QUEUE + '-1' in partitions)
        self.assertEqual(list(worker.partitioner), [queue_name + '-1'])
        worker.settings['partitions.ids'] = [queue_name + '-2']
        worker.configure_partitions()
        self.assertEqual(list(worker.partitioner), [queue_name + '-2'])

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
            raise StopWorker

        worker.job = job
        self._post_message(worker, queue_name, 'Hello')
        worker.work()
        self.assertTrue(worker.shutdown, True)

    def test_work_context(self):
        worker, queue_name = self._make_one()
        context = {}

        @contextmanager
        def job_context(context=context):
            context['counter'] = 0
            context['done'] = False
            try:
                yield context
            finally:
                context['done'] = True

        def job(message, context):
            context['counter'] += 1
            if message['body'] == 'end':
                raise StopWorker

        worker.job = job
        worker.job_context = job_context

        self._post_message(worker, queue_name, 'work')
        self._post_message(worker, queue_name, 'end')
        worker.work()
        self.assertEqual(context['counter'], 2)
        self.assertEqual(context['done'], True)

    def test_work_multiple_messages(self):
        worker, queue_name = self._make_one()
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] > 5:
                raise ValueError
            if message['body'] == 'end':
                raise StopWorker

        worker.job = job
        for i in range(4):
            self._post_message(worker, queue_name, 'work')
        time.sleep(0.02)
        self._post_message(worker, queue_name, 'end')

        worker.work()
        self.assertEqual(counter[0], 5)

    def test_work_multiple_queues(self):
        worker, queue_name = self._make_one()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, queue_name, 'queue1-1')
        self._post_message(worker, queue_name, 'queue1-2')
        self._post_message(worker, queue2, 'queue2-1')
        self._post_message(worker, queue2, 'queue2-2')
        self._post_message(worker, queue2, 'queue2-3')
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] == 5:
                raise StopWorker
            elif counter[0] > 5:
                raise ValueError

        worker.job = job
        worker.work()
        self.assertEqual(counter[0], 5)

    def test_work_multiple_empty_queues(self):
        worker, queue_name = self._make_one()
        worker.queuey_conn.create_queue()
        worker.queuey_conn.create_queue()
        queue2 = worker.queuey_conn.create_queue()
        self._post_message(worker, queue_name, 'queue1-1')
        self._post_message(worker, queue_name, 'queue1-2')
        self._post_message(worker, queue2, 'queue2-1')
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] == 3:
                raise StopWorker
            elif counter[0] > 3:
                raise ValueError

        worker.job = job
        worker.work()
        self.assertEqual(counter[0], 3)

    def test_work_multiple_queues_and_partitions(self):
        worker, queue_name = self._make_one()
        queuey_conn = worker.queuey_conn
        queue2 = queuey_conn.create_queue(partitions=3)
        self._post_message(worker, queue_name, ['1', '2'])
        # post messages to fill multiple partitions
        response = self._post_message(worker, queue2,
            ['%s' % i for i in xrange(8)])
        partitions = set([m['partition'] for m in
            ujson.decode(response.text)['messages']])
        # messages ended up in different partitions
        self.assertTrue(len(partitions) > 1, partitions)
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] == 10:
                raise StopWorker
            elif counter[0] > 10:
                raise ValueError

        worker.job = job
        worker.work()
        self.assertEqual(counter[0], 10)

    def test_job_failure_handler(self):
        worker, queue_name = self._make_one()
        context = {}

        @contextmanager
        def job_context(context=context):
            context['counter'] = 0
            context['errors'] = []
            yield context

        def job(message, context):
            context['counter'] += 1
            if context['counter'] == 1:
                raise ValueError('job failed')
            else:
                raise StopWorker

        def job_failure(message, context, name, exc, queuey_conn):
            context['errors'].append(exc)

        worker.job = job
        worker.job_context = job_context
        worker.job_failure = job_failure
        self._post_message(worker, queue_name, 'Fail')
        self._post_message(worker, queue_name, 'Finish')
        worker.work()
        errors = context['errors']
        self.assertEqual(len(errors), 1)
        self.assertTrue(isinstance(errors[0], ValueError))
        self.assertEqual(errors[0].args, ('job failed', ))

    def test_job_failure_save_handler(self):
        worker, queue_name = self._make_one(extra={
            'qdo-worker.job_failure': 'qdo.worker:save_failed_message'})
        queue2 = worker.queuey_conn.create_queue(partitions=10)
        self._post_message(worker, queue_name, ['-1', '-2'])
        self._post_message(worker, queue2,
            ['%s' % i for i in xrange(20)])
        counter = [0]

        def job(message, context, counter=counter):
            counter[0] += 1
            if counter[0] <= 20:
                raise ValueError('job failed: %s' % counter[0])
            else:
                raise StopWorker

        worker.job = job
        worker.work()

        partition_spec = ','.join(
            [unicode(i + 1) for i in range(STATUS_PARTITIONS)])
        failed_messages = worker.queuey_conn.messages(
            ERROR_QUEUE, partition=partition_spec)
        self.assertEqual(len(failed_messages), 20)
        error_partitions = [m['partition'] for m in failed_messages]
        # multiple error partitions are used, 20 messages aren't enough to
        # guarantee all 7 partitions get randomly selected
        self.assertTrue(len(set(error_partitions)) > 3)
        failures = [ujson.decode(m['body']) for m in failed_messages]
        # the first 20 of 22 failures get saved, two random ones aren't
        # processed
        data = set([int(f['body']) for f in failures])
        possible = set(xrange(-2, 20))
        self.assertTrue(data.issubset(possible))

    def test_multiple_workers(self):
        queuey_conn = self._queuey_conn
        events = []
        queues = []
        threads = []
        workers = []
        contexts = []
        lasts = []

        def job(message, context):
            if message['body'] == 'stop':
                raise StopWorker
            context.append(message['message_id'])

        for i in range(3):
            queue = queuey_conn.create_queue()
            queues.append(queue)
            worker, _ = self._make_one(extra={
                'qdo-worker.name': 'worker%s' % i,
                'partitions.policy': 'manual',
                'partitions.ids': [queue + '-1'],
            })

            @contextmanager
            def job_context(contexts=contexts):
                context = []
                contexts.append(context)
                yield context

            worker.job = job
            worker.job_context = job_context
            workers.append(worker)

            self._post_message(worker, queue,
                ['%s' % i for i in xrange(11)])
            response = self._post_message(worker, queue, 'last')
            last = ujson.decode(response.text)['messages'][0]['key']
            lasts.append(last)
            self._post_message(worker, queue, 'stop')

            event = threading.Event()
            events.append(event)

            def run(event):
                worker.work()
                event.set()

            thread = threading.Thread(target=run, args=(event, ))
            thread.start()
            threads.append(thread)

        for i in range(3):
            events[i].wait()
            self.assertEqual(contexts[i][-1], lasts[i])


class TestKazooWorker(BaseTestCase, KazooTestHarness):

    def setUp(self):
        BaseTestCase.setUp(self)
        self.setup_zookeeper()

    def tearDown(self):
        self.teardown_zookeeper()
        BaseTestCase.tearDown(self)

    def _make_one(self, extra=None, queue=True):
        extra = {} if not extra else extra
        extra['qdo-worker.wait_interval'] = 0
        extra['zookeeper.connection'] = self.hosts
        extra['zookeeper.party_wait'] = 0.5
        extra['partitions.policy'] = 'automatic'
        return _make_worker(self.queuey_app_key, extra=extra, queue=queue)

    def _post_message(self, worker, queue_name, data):
        queuey_conn = worker.queuey_conn
        return queuey_conn.post(queue_name, data=data)

    def test_work(self):
        worker, queue_name = self._make_one()
        counter = [0]

        def job(message, context):
            counter[0] += 1
            if counter[0] > 1:
                raise StopWorker

        worker.job = job
        self._post_message(worker, queue_name, ['1', '2'])
        worker.work()
        self.assertEqual([queue_name + '-1'], list(worker.partitioner))

    def test_multiple_workers(self):
        queuey_conn = self._queuey_conn
        events = []
        queues = []
        threads = []
        workers = []

        def job(message, context):
            if message['body'] == 'stop':
                raise StopWorker

        for i in range(3):
            queue = queuey_conn.create_queue(partitions=9)
            queues.append(queue)

        # wait for all queues to be created
        time.sleep(0.5)
        for i in range(3):
            worker, _ = self._make_one(extra={
                'qdo-worker.name': 'worker%s' % i}, queue=False)

            worker.job = job
            workers.append(worker)

            self._post_message(worker, queues[i],
                ['%s' % j for j in xrange(20)])
            self._post_message(worker, queues[i],
                ['stop' for j in xrange(20)])

            event = threading.Event()
            events.append(event)

            def run(event):
                worker.work()
                event.set()

            thread = threading.Thread(target=run, args=(event, ))
            thread.start()
            threads.append(thread)

        for i in range(3):
            events[i].wait(2)

        all_partitions = []
        for i in range(3):
            partitions = list(workers[i].partitioner)
            workers[i].stop()
            threads[i].join()
            self.assertTrue(len(partitions) > 3)
            all_partitions.extend(partitions)

        self.assertEqual(len(set(all_partitions)), 27)
