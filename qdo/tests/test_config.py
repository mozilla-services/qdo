# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest


class TestConfig(unittest.TestCase):

    def _make_one(self, extra=None):
        from qdo.config import QdoSettings
        settings = QdoSettings()
        if extra is not None:
            settings.update(extra)
        return settings

    def test_defaults(self):
        settings = self._make_one()
        qdo_section = settings.getsection(u'qdo-worker')
        self.assertEqual(qdo_section[u'wait_interval'], 30)
        self.assertEqual(qdo_section[u'name'], u'')
        queuey_section = settings.getsection(u'queuey')
        self.assertEqual(queuey_section[u'connection'],
            u'http://127.0.0.1:5000/v1/queuey/')

    def test_configure(self):
        extra = {
            u'qdo-worker.wait_interval': 1,
            u'queuey.url': u'https://10.0.0.1:2345',
            }
        settings = self._make_one(extra)
        qdo_section = settings.getsection(u'qdo-worker')
        self.assertEqual(qdo_section[u'wait_interval'], 1)
        queuey_section = settings.getsection(u'queuey')
        self.assertEqual(queuey_section[u'url'], u'https://10.0.0.1:2345')

    def test_manual_partition(self):
        extra = {
            u'partitions.policy': u'manual',
            u'partitions.ids': [u'a4bb2fb6dcda4b68aad743a4746d7f58-1'],
            }
        settings = self._make_one(extra)
        p_section = settings.getsection(u'partitions')
        self.assertEqual(p_section[u'policy'], u'manual')
        self.assertEqual(
            p_section[u'ids'], [u'a4bb2fb6dcda4b68aad743a4746d7f58-1'])
