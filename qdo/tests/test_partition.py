# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from qdo.tests.base import BaseTestCase


class TestPartition(BaseTestCase):

    def _make_one(self):
        from qdo.partition import Partition
        self.conn = self._make_queuey_conn()
        self.queue_name = self.conn._create_queue()
        self.partition = Partition(self.conn, self.queue_name)
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

    def test_timestamp_get(self):
        partition = self._make_one()
        self.assertEqual(partition.timestamp, 0.0)

    def test_timestamp_set(self):
        partition = self._make_one()
        partition.timestamp = 1331231353.762148
        self.assertEqual(partition.timestamp, 1331231353.762148)

    def test_timestamp_set_string(self):
        partition = self._make_one()
        partition.timestamp = u'1331231353.762148'.encode(u'utf-8')
        self.assertEqual(partition.timestamp, 1331231353.762148)

    def test_timestamp_set_unicode(self):
        partition = self._make_one()
        partition.timestamp = u'1331231353.762148'
        self.assertEqual(partition.timestamp, 1331231353.762148)
