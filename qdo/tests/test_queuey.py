# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from qdo import testing
if not testing.CASSANDRA:
    import nose
    raise nose.SkipTest

import time
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

    def test_configure_connection(self):
        conn = self._make_one()
        self.assertEqual(conn.app_url, u'https://127.0.0.1:5001/v1/queuey/')

    def test_configure_connection_multiple(self):
        servers = [u'127.0.0.1:5001', u'127.0.0.1:5002', u'127.0.0.1:5003']
        servers = [u'https://%s/v1/queuey/' % s for s in servers]
        conn = self._make_one(u','.join(servers))
        self.assertTrue(conn.app_url in servers)

    def test_configure_connection_multiple_nonlocal(self):
        servers = [u'10.0.0.1:5001', u'10.0.0.1:5002', u'10.0.0.1:5003']
        servers = [u'https://%s/v1/queuey/' % s for s in servers]
        conn = self._make_one(u','.join(servers))
        self.assertTrue(conn.app_url in servers)

    def test_configure_connection_multiple_preferlocal(self):
        servers = [u'10.0.0.1:5001', u'10.0.0.1:5002', u'127.0.0.1:5001']
        servers = [u'https://%s/v1/queuey/' % s for s in servers]
        conn = self._make_one(u','.join(servers))
        self.assertEqual(conn.app_url, u'https://127.0.0.1:5001/v1/queuey/')

    def test_configure_connection_multiple_preferlocal_many(self):
        local = [u'127.0.0.1:5001', u'localhost:5002', u'::1:5001']
        local = [u'https://%s/v1/queuey/' % s for s in local]
        remote = [u'svc1.mozilla.org:5001', u'10.0.0.1:5001']
        remote = [u'https://%s/v1/queuey/' % s for s in remote]
        servers = local + remote
        conn = self._make_one(u','.join(servers))
        self.assertTrue(conn.app_url in local, conn.app_url)
        servers.remove(conn.app_url)
        self.assertEqual(conn.fallback_urls, servers)

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
        name = conn.create_queue()
        response = conn.delete(name)
        self.assertEqual(response.status_code, 200)
        response = conn.get()
        queues = ujson.decode(response.text)[u'queues']
        self.assertTrue(name not in queues)

    def test_delete_timeout(self):
        conn = self._make_one()
        name = conn.create_queue()
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
        name = conn.create_queue()
        response = conn.delete(name)
        self.assertEqual(response.status_code, 200)

    def test_post_messages(self):
        conn = self._make_one()
        name = conn.create_queue()
        response = conn.post(name, data=[u'a', u'b', u'c'])
        self.assertEqual(response.status_code, 201)
        result = ujson.decode(response.text)
        self.assertEqual(len(result[u'messages']), 3, result)

    def test_create_queue(self):
        conn = self._make_one()
        name = conn.create_queue()
        response = ujson.decode(conn.get(params={u'details': True}).text)
        queues = response[u'queues']
        info = [q for q in queues if q[u'queue_name'] == name][0]
        self.assertEqual(info[u'partitions'], 1)

    def test_create_queue_partitions(self):
        conn = self._make_one()
        name = conn.create_queue(partitions=3)
        response = ujson.decode(conn.get(params={u'details': True}).text)
        queues = response[u'queues']
        info = [q for q in queues if q[u'queue_name'] == name][0]
        self.assertEqual(info[u'partitions'], 3)

    def test_create_queue_name(self):
        conn = self._make_one()
        name = conn.create_queue(queue_name=u'test-queue')
        response = ujson.decode(conn.get(params={u'details': True}).text)
        queues = response[u'queues']
        info = [q for q in queues if q[u'queue_name'] == name][0]
        self.assertEqual(info[u'partitions'], 1)

    def test_create_queue_error(self):
        from qdo.exceptions import HTTPError
        conn = self._make_one()
        self.assertRaises(HTTPError, conn.create_queue, **dict(partitions=-1))

    def test_messages(self):
        conn = self._make_one()
        name = conn.create_queue()
        # add test message
        conn.post(url=name, data=u'Hello world!')
        # query
        messages = conn.messages(name)
        bodies = [m[u'body'] for m in messages]
        self.assertTrue(u'Hello world!' in bodies)

    def test_messages_since(self):
        conn = self._make_one()
        name = conn.create_queue()
        # add test message
        conn.post(url=name, data=u'Hello')
        # query messages in the future
        messages = conn.messages(name, since=time.time() + 1000)
        self.assertEqual(len(messages), 0)

    def test_messages_error(self):
        from qdo.exceptions import HTTPError
        conn = self._make_one()
        name = conn.create_queue()
        try:
            conn.messages(name, order=u'undefined')
        except HTTPError, e:
            self.assertEqual(e.args[0], 400)
            messages = ujson.decode(e.args[1].text)[u'error_msg']
            self.assertTrue(u'order' in messages, messages)
        else:
            self.fail(u'HTTPError not raised')

    def test_partitions(self):
        conn = self._make_one()
        queue_name = conn.create_queue(partitions=3)
        partitions = conn._partitions()
        expected = [queue_name + u'-' + unicode(i) for i in range(1, 4)]
        self.assertTrue(set(expected).issubset(set(partitions)))
