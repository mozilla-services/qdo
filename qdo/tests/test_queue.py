# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import time
import unittest2 as unittest

import requests

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueueyConnection(unittest.TestCase):

    def _make_one(self, server_url='http://127.0.0.1:5000'):
        from qdo.queue import QueueyConnection
        return QueueyConnection(
            server_url=server_url, application_key=TEST_APP_KEY)

    def test_connect(self):
        conn = self._make_one()
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_fail(self):
        conn = self._make_one(server_url='http://127.0.0.1:9')
        self.assertRaises(requests.ConnectionError, conn.connect)

    def test_queue_list(self):
        conn = self._make_one()
        response = conn.get()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('queues' in response.text, response.text)

    def test_queue_create(self):
        conn = self._make_one()
        response = conn.post()
        self.assertEqual(response.status_code, 201)
        result = json.loads(response.text)
        self.assertTrue(u'queue_name' in result, result)


class TestQueue(unittest.TestCase):

    def _make_one(self):
        from qdo.queue import Queue, QueueyConnection
        self.conn = QueueyConnection(application_key=TEST_APP_KEY)
        response = self.conn.post()
        result = json.loads(response.text)
        self.queue_name = result[u'queue_name']
        self.queue = Queue(self.conn, self.queue_name)
        return self.queue

    def test_get(self):
        queue = self._make_one()
        test_message = {u'body': u'Hello world!'}
        # add test message
        response = self.conn.post(url=self.queue_name, data=test_message)
        # query
        time.sleep(0.01)
        result = json.loads(queue.get())
        self.assertTrue(u'messages' in result)
        bodies = [m[u'body'] for m in result[u'messages']]
        self.assertTrue(u'Hello world!' in bodies)

    @unittest.expectedFailure
    def test_get_since(self):
        queue = self._make_one()
        # query messages in the future
        result = queue.get(since=str(int(time.time() + 1000)))
        self.assertTrue(u'messages' in result)
        self.assertEqual(len(result[u'messages']), 0)
