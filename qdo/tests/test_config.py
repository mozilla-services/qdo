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
        self.assertEqual(qdo_section[u'wait_interval'], 5)
        queuey_section = settings.getsection(u'queuey')
        self.assertEqual(queuey_section[u'connection'],
            u'https://127.0.0.1:5001/v1/queuey/')
        zk_section = settings.getsection(u'zookeeper')
        self.assertEqual(zk_section[u'connection'],
            u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187/mozilla-qdo')

    def test_configure(self):
        extra = {
            u'qdo-worker.wait_interval': 30,
            u'queuey.url': u'https://10.0.0.1:2345',
            u'zookeeper.connection': u'10.0.0.2:3456/qdo',
            }
        settings = self._make_one(extra)
        qdo_section = settings.getsection(u'qdo-worker')
        self.assertEqual(qdo_section[u'wait_interval'], 30)
        queuey_section = settings.getsection(u'queuey')
        self.assertEqual(queuey_section[u'url'], u'https://10.0.0.1:2345')
        zk_section = settings.getsection(u'zookeeper')
        self.assertEqual(zk_section[u'connection'], u'10.0.0.2:3456/qdo')
