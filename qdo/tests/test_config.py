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
        from qdo import config
        settings = self._make_one()
        qdo_section = settings.getsection('qdo-worker')
        self.assertEqual(qdo_section['wait_interval'], 30)
        self.assertEqual(qdo_section['name'], '')
        queuey_section = settings.getsection('queuey')
        self.assertEqual(queuey_section['connection'],
            'http://127.0.0.1:5000/v1/queuey/')
        zk_section = settings.getsection('zookeeper')
        self.assertEqual(zk_section['connection'], config.ZOO_DEFAULT_CONN)

    def test_configure(self):
        extra = {
            'qdo-worker.wait_interval': 1,
            'queuey.url': 'https://10.0.0.1:2345',
            'zookeeper.connection': '10.0.0.2:3456/qdo',
        }
        settings = self._make_one(extra)
        qdo_section = settings.getsection('qdo-worker')
        self.assertEqual(qdo_section['wait_interval'], 1)
        queuey_section = settings.getsection('queuey')
        self.assertEqual(queuey_section['url'], 'https://10.0.0.1:2345')
        zk_section = settings.getsection('zookeeper')
        self.assertEqual(zk_section['connection'], '10.0.0.2:3456/qdo')

    def test_manual_partition(self):
        extra = {
            'partitions.policy': 'manual',
            'partitions.ids': ['a4bb2fb6dcda4b68aad743a4746d7f58-1'],
        }
        settings = self._make_one(extra)
        p_section = settings.getsection('partitions')
        self.assertEqual(p_section['policy'], 'manual')
        self.assertEqual(
            p_section['ids'], ['a4bb2fb6dcda4b68aad743a4746d7f58-1'])
