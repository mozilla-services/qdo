# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import unittest

HERE = os.path.dirname(__file__)
DATA_DIR = os.path.join(HERE, 'data')
TEST_CONFIG = os.path.join(DATA_DIR, 'test.conf')


class TestConfigParser(unittest.TestCase):

    def test_parse_config(self):
        from qdo.runner import parse_config
        settings = {}
        config = parse_config(TEST_CONFIG, settings)
        self.assertEqual(config.sections(), ['qdo-worker'])
        self.assertEqual(settings['qdo-worker.wait_interval'], 10)

    def test_parse_config_nofile(self):
        from qdo.runner import parse_config
        settings = {}
        config = parse_config(os.path.join(DATA_DIR, 'none'), settings)
        self.assertTrue(config is None)
        self.assertEqual(settings, {})


class TestArgsParser(unittest.TestCase):

    def test_parse_args(self):
        from qdo.runner import parse_args, DEFAULT_CONFIGFILE
        namespace = parse_args([])
        self.assertEqual(namespace.configfile, DEFAULT_CONFIGFILE)

    def test_parse_args_configfile(self):
        from qdo.runner import parse_args
        namespace = parse_args(['-c', TEST_CONFIG])
        self.assertEqual(namespace.configfile, TEST_CONFIG)
