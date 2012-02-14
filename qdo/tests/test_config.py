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

    def test_configure(self):
        extra = {'qdo-worker.wait_interval': 30}
        settings = self._make_one(extra)
        qdo_section = settings.getsection('qdo-worker')
        self.assertEqual(qdo_section['wait_interval'], 30)
