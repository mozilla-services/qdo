# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

import mock
import requests


class TestQueueyConnection(unittest.TestCase):

    def _make_one(self, **kwargs):
        from qdo.queue import QueueyConnection
        return QueueyConnection(**kwargs)

    def test_init(self):
        conn = self._make_one(server_url='http://127.0.0.1:1234')
        self.assertEqual(conn.server_url, 'http://127.0.0.1:1234')

    def test_connect(self):
        conn = self._make_one(server_url='http://127.0.0.1:9')
        self.assertRaises(requests.ConnectionError, conn.connect)


class TestQueue(unittest.TestCase):

    def _make_one(self):
        from qdo.queue import Queue, QueueyConnection
        conn = QueueyConnection()
        return Queue(conn, '1234')

    def test_get(self):
        queue = self._make_one()
        test_message = json.dumps({u'msgid': 1})
        with mock.patch('qdo.queue.QueueyConnection.get') as get_mock:
            get_mock.return_value.text = unicode(test_message, 'utf-8')
            get_mock.return_value.status_code = 200
            message = queue.get()
        self.assertTrue(message)
        self.assertEqual(message, test_message)
