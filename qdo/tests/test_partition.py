# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from qdo.config import STATUS_QUEUE
from qdo.tests.base import BaseTestCase


class TestPartition(BaseTestCase):

    dummy_uuid = 'a8f70ab3cb7411e19621b88d120c81de'

    def _make_one(self):
        from qdo.partition import Partition
        self.conn = self._make_queuey_conn()
        self.queue_name = self.conn.create_queue()
        self.conn.create_queue(queue_name=STATUS_QUEUE)
        self.partition = Partition(self.conn, self.queue_name)
        return self.partition

    def test_name(self):
        partition = self._make_one()
        self.assertTrue(partition.name.startswith(self.queue_name))

    def test_messages(self):
        partition = self._make_one()
        # add test message
        self.conn.post(url=self.queue_name, data='Hello world!')
        # query
        messages = partition.messages()
        bodies = [m['body'] for m in messages]
        self.assertTrue('Hello world!' in bodies)

    def test_last_message_get(self):
        partition = self._make_one()
        self.assertEqual(partition.last_message, '')

    def test_last_message_set(self):
        partition = self._make_one()
        partition.last_message = self.dummy_uuid
        self.assertEqual(partition.last_message, self.dummy_uuid)

    def test_last_message_set_string(self):
        partition = self._make_one()
        partition.last_message = self.dummy_uuid.encode('utf-8')
        self.assertEqual(partition.last_message, self.dummy_uuid)
