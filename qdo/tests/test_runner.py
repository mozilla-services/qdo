# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import unittest

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, 'data')


class TestConfigParser(unittest.TestCase):

    def test_parse_config(self):
        from qdo.runner import parse_config
        test_config = os.path.join(DATA_DIR, 'test.conf')
        settings = {}
        config = parse_config(test_config, settings)
        self.assertEqual(config.sections(), ['qdo-worker'])
        self.assertEqual(settings['qdo-worker.wait_interval'], 10)

    def test_parse_config_nofile(self):
        from qdo.runner import parse_config
        settings = {}
        config = parse_config(os.path.join(DATA_DIR, 'none'), settings)
        self.assertTrue(config is None)
        self.assertEqual(settings, {})
