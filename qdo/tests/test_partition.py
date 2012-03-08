# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from requests.exceptions import HTTPError
import ujson
import unittest2 as unittest

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueue(unittest.TestCase):

    def tearDown(self):
        del self.partition
        del self.queue_name

    def _make_one(self):
        from qdo.partition import Partition
        from qdo.queuey import QueueyConnection
        self.conn = QueueyConnection(TEST_APP_KEY)
        self.queue_name = self.conn._create_queue()
        self.partition = Partition(self.conn, self.queue_name)
        return self.partition

    def test_name(self):
        partition = self._make_one()
        self.assertTrue(partition.name.startswith(self.queue_name))

    def test_get(self):
        partition = self._make_one()
        test_message = u'Hello world!'
        # add test message
        self.conn.post(url=self.queue_name, data=test_message)
        # query
        result = partition.get()
        self.assertTrue(u'messages' in result)
        bodies = [m[u'body'] for m in result[u'messages']]
        self.assertTrue(u'Hello world!' in bodies)

    def test_get_since(self):
        partition = self._make_one()
        # query messages in the future
        result = partition.get(since=time.time() + 1000)
        self.assertTrue(u'messages' in result)
        self.assertEqual(len(result[u'messages']), 0)

    def test_get_error(self):
        partition = self._make_one()
        try:
            partition.get(order='undefined')
        except HTTPError, e:
            self.assertEqual(e.args[0], 400)
            messages = ujson.decode(e.args[1].text)[u'error_msg']
            self.assertTrue(u'order' in messages, messages)
        else:
            self.fail('HTTPError not raised')
