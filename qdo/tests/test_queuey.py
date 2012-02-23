# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

import mock
from requests.exceptions import ConnectionError
from requests.exceptions import Timeout

from qdo import utils

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueueyConnection(unittest.TestCase):

    def _make_one(self, server_url='http://127.0.0.1:5000'):
        from qdo.queuey import QueueyConnection
        return QueueyConnection(
            server_url=server_url, application_key=TEST_APP_KEY)

    def test_connect(self):
        conn = self._make_one()
        response = conn.connect()
        self.assertEqual(response.status_code, 200)

    def test_connect_fail(self):
        conn = self._make_one(server_url='http://127.0.0.1:9')
        self.assertRaises(ConnectionError, conn.connect)

    def test_connect_timeout(self):
        conn = self._make_one()
        before = len(utils.metsender.msgs)
        with mock.patch('requests.sessions.Session.head') as head_mock:
            head_mock.side_effect = Timeout
            self.assertRaises(Timeout, conn.connect)
            self.assertEqual(len(head_mock.mock_calls), conn.retries)
        self.assertEqual(len(utils.metsender.msgs), before + 3)

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
