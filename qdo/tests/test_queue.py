# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import time

from requests.exceptions import HTTPError
import unittest2 as unittest

# as specified in the queuey-dev.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


class TestQueue(unittest.TestCase):

    def _make_one(self):
        from qdo.queue import Queue
        from qdo.queuey import QueueyConnection
        self.conn = QueueyConnection(application_key=TEST_APP_KEY)
        response = self.conn.post()
        result = json.loads(response.text)
        self.queue_name = result[u'queue_name']
        self.queue = Queue(self.conn, self.queue_name)
        return self.queue

    def test_get(self):
        queue = self._make_one()
        test_message = u'Hello world!'
        # add test message
        self.conn.post(url=self.queue_name, data=test_message)
        # query
        time.sleep(0.01)
        result = json.loads(queue.get())
        self.assertTrue(u'messages' in result)
        bodies = [m[u'body'] for m in result[u'messages']]
        self.assertTrue(u'Hello world!' in bodies)

    def test_get_since(self):
        queue = self._make_one()
        # query messages in the future
        result = json.loads(queue.get(since=time.time() + 1000))
        self.assertTrue(u'messages' in result)
        self.assertEqual(len(result[u'messages']), 0)

    def test_get_error(self):
        queue = self._make_one()
        try:
            queue.get(order='undefined')
        except HTTPError, e:
            self.assertEqual(e.args[0], 400)
            messages = json.loads(e.args[1].text)[u'error_msg']
            self.assertTrue(u'order' in messages, messages)
        else:
            self.fail('HTTPError not raised')
