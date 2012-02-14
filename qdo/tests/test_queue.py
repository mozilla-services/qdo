# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest


class TestQueueyConnection(unittest.TestCase):

    def _make_one(self):
        from qdo.queue import QueueyConnection
        return QueueyConnection()

    def test_init(self):
        conn = self._make_one()
        self.assertTrue(conn)


class TestQueue(unittest.TestCase):

    def _make_one(self):
        from qdo.queue import Queue, QueueyConnection
        conn = QueueyConnection()
        return Queue(conn)

    def test_pop(self):
        queue = self._make_one()
        test_message = json.dumps({'msgid': 1})
        queue._add(test_message)
        message = queue.pop()
        self.assertTrue(message)
        self.assertEqual(message, test_message)
