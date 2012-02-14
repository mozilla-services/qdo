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
        qdo_section = settings.getsection('qdo-worker')
        self.assertEqual(qdo_section['wait_interval'], 5)
        queuey_section = settings.getsection('queuey')
        self.assertEqual(queuey_section['url'], 'http://127.0.0.1:5000')
        zk_section = settings.getsection('zookeeper')
        self.assertEqual(zk_section['connection'], '127.0.0.1:2181')

    def test_configure(self):
        extra = {
            'qdo-worker.wait_interval': 30,
            'queuey.url': 'https://10.0.0.1:2345',
            'zookeeper.connection': '10.0.0.2:3456',
            }
        settings = self._make_one(extra)
        qdo_section = settings.getsection('qdo-worker')
        self.assertEqual(qdo_section['wait_interval'], 30)
        queuey_section = settings.getsection('queuey')
        self.assertEqual(queuey_section['url'], 'https://10.0.0.1:2345')
        zk_section = settings.getsection('zookeeper')
        self.assertEqual(zk_section['connection'], '10.0.0.2:3456')
