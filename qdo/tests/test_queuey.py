# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from qdo import testing
if not testing.CASSANDRA:
    import nose
    raise nose.SkipTest

import unittest

import mock
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout
import ujson

from qdo.log import get_logger
from qdo.tests.base import QueueyBase


class TestQueueyConnection(unittest.TestCase, QueueyBase):

    @classmethod
    def setUpClass(cls):
        QueueyBase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        QueueyBase.tearDownClass()

    def setUp(self):
        QueueyBase._clean_queuey()

    def _make_one(self, connection=u'https://127.0.0.1:5001/v1/queuey/'):
        return self._make_queuey_conn(connection=connection)

    def test_connect(self):
        conn = self._make_one()
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_fail(self):
        conn = self._make_one(connection=u'https://127.0.0.1:9/')
        self.assertRaises(ConnectionError, conn.connect)

    def test_connect_timeout(self):
        conn = self._make_one()
        metlog = get_logger()
        before = len(metlog.sender.msgs)
        with mock.patch(u'requests.sessions.Session.head') as head_mock:
            head_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.connect)
            self.assertEqual(len(head_mock.mock_calls), conn.retries)
        self.assertEqual(len(metlog.sender.msgs), before + 3)

    def test_connect_multiple(self):
        conn = self._make_one(connection=u'https://127.0.0.1:5001/v1/queuey/,'
            u'https://127.0.0.1:5002/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_multiple_first_unreachable(self):
        conn = self._make_one(connection=u'https://127.0.0.1:9/,'
            u'https://127.0.0.1:5002/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_multiple_first_invalid_ssl(self):
        conn = self._make_one(connection=u'https://127.0.0.1:5003/v1/queuey/,'
            u'https://127.0.0.1:5001/v1/queuey/')
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_get(self):
        conn = self._make_one()
        response = conn.get()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(u'queues' in response.text, response.text)

    def test_get_timeout(self):
        conn = self._make_one()
        metlog = get_logger()
        before = len(metlog.sender.msgs)
        with mock.patch(u'requests.sessions.Session.get') as get_mock:
            get_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.get)
            self.assertEqual(len(get_mock.mock_calls), conn.retries)
        self.assertEqual(len(metlog.sender.msgs), before + 3)

    def test_get_multiple_first_unreachable(self):
        conn = self._make_one(connection=u'https://127.0.0.1:9/,'
            u'https://127.0.0.1:5002/v1/queuey/')
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
        metlog = get_logger()
        before = len(metlog.sender.msgs)
        with mock.patch(u'requests.sessions.Session.post') as post_mock:
            post_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.post)
            self.assertEqual(len(post_mock.mock_calls), conn.retries)
        self.assertEqual(len(metlog.sender.msgs), before + 3)

    def test_post_multiple_first_unreachable(self):
        conn = self._make_one(connection=u'https://127.0.0.1:9/,'
            u'https://127.0.0.1:5002/v1/queuey/')
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
        metlog = get_logger()
        before = len(metlog.sender.msgs)
        with mock.patch(u'requests.sessions.Session.delete') as delete_mock:
            delete_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.delete, name)
            self.assertEqual(len(delete_mock.mock_calls), conn.retries)
        self.assertEqual(len(metlog.sender.msgs), before + 3)

    def test_delete_multiple_first_unreachable(self):
        conn = self._make_one(connection=u'https://127.0.0.1:9/,'
            u'https://127.0.0.1:5002/v1/queuey/')
        name = conn._create_queue()
        response = conn.delete(name)
        self.assertEqual(response.status_code, 200)

    def test_post_messages(self):
        conn = self._make_one()
        name = conn._create_queue()
        response = conn.post(name, data=[u'a', u'b', u'c'])
        self.assertEqual(response.status_code, 201)
        result = ujson.decode(response.text)
        self.assertEqual(len(result[u'messages']), 3, result)

    def test_create_queue(self):
        conn = self._make_one()
        name = conn._create_queue()
        response = ujson.decode(conn.get(params={u'details': True}).text)
        queues = response[u'queues']
        info = [q for q in queues if q[u'queue_name'] == name][0]
        self.assertEqual(info[u'partitions'], 1)

    def test_create_queue_partitions(self):
        conn = self._make_one()
        name = conn._create_queue(partitions=3)
        response = ujson.decode(conn.get(params={u'details': True}).text)
        queues = response[u'queues']
        info = [q for q in queues if q[u'queue_name'] == name][0]
        self.assertEqual(info[u'partitions'], 3)

    def test_partitions(self):
        conn = self._make_one()
        queue_name = conn._create_queue(partitions=3)
        partitions = conn._partitions()
        expected = [queue_name + u'-' + unicode(i) for i in range(1, 4)]
        self.assertTrue(set(expected).issubset(set(partitions)))
