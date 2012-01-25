# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest

from mozsvc.config import SettingsDict


class TestWorker(unittest.TestCase):

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

    def test_work(self):
        worker = self._make_one()
        worker.shutdown = True
        worker.work()
        self.assertEqual(worker.shutdown, True)
