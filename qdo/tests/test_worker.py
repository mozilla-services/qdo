# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
import unittest

from mozsvc.config import SettingsDict
from zktools.connection import ZkConnection


class TestWorkerConfig(unittest.TestCase):

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = SettingsDict()
        if extra is not None:
            settings.update(extra)
        return Worker(settings)

    def test_configure(self):
        extra = {'qdo-worker.wait_interval': 30}
        worker = self._make_one(extra)
        self.assertEqual(worker.wait_interval, 30)

    def test_work_shutdown(self):
        worker = self._make_one()
        worker.shutdown = True
        worker.work()
        self.assertEqual(worker.shutdown, True)


class TestWorker(unittest.TestCase):

    def setUp(self):
        zkconn = ZkConnection(host='localhost:2181')
        zkconn.connect()
        if zkconn.exists('/workers'):
            zkconn.delete('/workers')
        zkconn.close()

    def _make_one(self, extra=None):
        from qdo.worker import Worker
        settings = SettingsDict()
        if extra is not None:
            settings.update(extra)
        return Worker(settings)

    def test_work(self):
        worker = self._make_one()
        worker.messages.append(json.dumps({'msgid': 1}))
        worker.messages.append(json.dumps({'msgid': 2}))

        def stop(message):
            raise KeyboardInterrupt

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(len(worker.messages), 1)

    def test_work_twice(self):
        worker = self._make_one()
        worker.messages.append(json.dumps({'msgid': 1}))
        worker.messages.append(json.dumps({'msgid': 2}))

        def stop(message):
            data = json.loads(message)
            if data['msgid'] == 1:
                # process the first message
                return
            raise KeyboardInterrupt

        worker.job = stop
        self.assertRaises(KeyboardInterrupt, worker.work)
        self.assertEqual(len(worker.messages), 0)
