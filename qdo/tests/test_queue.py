# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

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
        return Queue(conn)

    def test_get(self):
        queue = self._make_one()
        test_message = json.dumps({'msgid': 1})
        queue._add(test_message)
        message = queue.get()
        self.assertTrue(message)
        self.assertEqual(message, test_message)
