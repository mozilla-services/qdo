# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from requests.exceptions import HTTPError
import ujson
import unittest2 as unittest
from zktools.node import ZkNode

from qdo.tests.base import ZKBase

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueue(unittest.TestCase, ZKBase):

    @classmethod
    def setUpClass(cls):
        ZKBase.setUpClass()
        cls.zk_conn = cls._make_zk_conn()

    @classmethod
    def tearDownClass(cls):
        cls.zk_conn.close()
        ZKBase.tearDownClass()

    def setUp(self):
        ZKBase._clean_zk(self.zk_conn)
        ZkNode(self.zk_conn, u'/partitions')

    def tearDown(self):
        del self.partition
        del self.queue_name

    def _make_one(self):
        from qdo.partition import Partition
        from qdo.queuey import QueueyConnection
        self.conn = QueueyConnection(TEST_APP_KEY)
        self.queue_name = self.conn._create_queue()
        self.partition = Partition(self.conn, self.zk_conn, self.queue_name)
        return self.partition

    def test_name(self):
        partition = self._make_one()
        self.assertTrue(partition.name.startswith(self.queue_name))

    def test_messages(self):
        partition = self._make_one()
        # add test message
        self.conn.post(url=self.queue_name, data=u'Hello world!')
        # query
        messages = partition.messages()
        bodies = [m[u'body'] for m in messages]
        self.assertTrue(u'Hello world!' in bodies)

    def test_messages_since(self):
        partition = self._make_one()
        # add test message
        self.conn.post(url=self.queue_name, data=u'Hello')
        # query messages in the future
        partition.timestamp = time.time() + 1000
        messages = partition.messages()
        self.assertEqual(len(messages), 0)

    def test_messages_error(self):
        partition = self._make_one()
        try:
            partition.messages(order='undefined')
        except HTTPError, e:
            self.assertEqual(e.args[0], 400)
            messages = ujson.decode(e.args[1].text)[u'error_msg']
            self.assertTrue(u'order' in messages, messages)
        else:
            self.fail('HTTPError not raised')

    def test_timestamp_get(self):
        partition = self._make_one()
        self.assertEqual(partition.timestamp, 0.0)

    def test_timestamp_set(self):
        partition = self._make_one()
        partition.timestamp = 1331231353.762148
        self.assertEqual(partition.timestamp, 1331231353.762148)

    def test_timestamp_set_string(self):
        partition = self._make_one()
        partition.timestamp = '1331231353.762148'
        self.assertEqual(partition.timestamp, 1331231353.762148)

    def test_timestamp_set_unicode(self):
        partition = self._make_one()
        partition.timestamp = u'1331231353.762148'
        self.assertEqual(partition.timestamp, 1331231353.762148)
