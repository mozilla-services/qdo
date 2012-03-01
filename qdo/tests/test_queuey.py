# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

import mock
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
import ujson

from qdo import utils

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueueyConnection(unittest.TestCase):

    conn = None

    def tearDown(self):
        if self.conn:
            try:
                response = self.conn.get()
                queues = ujson.decode(response.text)[u'queues']
                names = [q[u'queue_name'] for q in queues]
                for n in names:
                    self.conn.delete(n)
            except ConnectionError:
                pass

    def _make_one(self, connection='https://127.0.0.1:5001/v1/queuey/'):
        from qdo.queuey import QueueyConnection
        self.conn = QueueyConnection(TEST_APP_KEY, connection=connection)
        return self.conn

    def test_connect(self):
        conn = self._make_one()
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_fail(self):
        conn = self._make_one(connection='https://127.0.0.1:9/')
        self.assertRaises(ConnectionError, conn.connect)

    def test_connect_timeout(self):
        conn = self._make_one()
        before = len(utils.metsender.msgs)
        with mock.patch('requests.sessions.Session.head') as head_mock:
            head_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.connect)
            self.assertEqual(len(head_mock.mock_calls), conn.retries)
        self.assertEqual(len(utils.metsender.msgs), before + 3)

    def test_connect_multiple(self):
        conn = self._make_one(connection='https://127.0.0.1:5001/v1/queuey/,'
            'https://127.0.0.1:5002/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_multiple_first_unreachable(self):
        conn = self._make_one(connection='https://127.0.0.1:9/,'
            'https://127.0.0.1:5002/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_multiple_first_invalid_ssl(self):
        conn = self._make_one(connection='https://127.0.0.1:5003/v1/queuey/,'
            'https://127.0.0.1:5001/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        conn = self._make_one()
        response = conn.get()
        self.assertEqual(response.status_code, 200)
        self.assertTrue('queues' in response.text, response.text)

    def test_get_timeout(self):
        conn = self._make_one()
        before = len(utils.metsender.msgs)
        with mock.patch('requests.sessions.Session.get') as get_mock:
            get_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.get)
            self.assertEqual(len(get_mock.mock_calls), conn.retries)
        self.assertEqual(len(utils.metsender.msgs), before + 3)

    def test_get_multiple_first_unreachable(self):
        conn = self._make_one(connection='https://127.0.0.1:9/,'
            'https://127.0.0.1:5002/v1/queuey/')
        response = conn.get()
        self.assertEqual(response.status_code, 200)

    def test_post(self):
        conn = self._make_one()
        response = conn.post()
        self.assertEqual(response.status_code, 201)
        result = ujson.decode(response.text)
        self.assertTrue(u'queue_name' in result, result)

    def test_post_timeout(self):
        conn = self._make_one()
        before = len(utils.metsender.msgs)
        with mock.patch('requests.sessions.Session.post') as post_mock:
            post_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.post)
            self.assertEqual(len(post_mock.mock_calls), conn.retries)
        self.assertEqual(len(utils.metsender.msgs), before + 3)

    def test_post_multiple_first_unreachable(self):
        conn = self._make_one(connection='https://127.0.0.1:9/,'
            'https://127.0.0.1:5002/v1/queuey/')
        response = conn.post()
        self.assertEqual(response.status_code, 201)

    def test_delete(self):
        conn = self._make_one()
        name = conn._create_queue()
        response = conn.delete(name)
        self.assertEqual(response.status_code, 200)
        response = conn.get()
        queues = ujson.decode(response.text)[u'queues']
        self.assertTrue(name not in queues)

    def test_delete_timeout(self):
        conn = self._make_one()
        name = conn._create_queue()
        before = len(utils.metsender.msgs)
        with mock.patch('requests.sessions.Session.delete') as delete_mock:
            delete_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.delete, name)
            self.assertEqual(len(delete_mock.mock_calls), conn.retries)
        self.assertEqual(len(utils.metsender.msgs), before + 3)

    def test_delete_multiple_first_unreachable(self):
        conn = self._make_one(connection='https://127.0.0.1:9/,'
            'https://127.0.0.1:5002/v1/queuey/')
        name = conn._create_queue()
        response = conn.delete(name)
        self.assertEqual(response.status_code, 200)
