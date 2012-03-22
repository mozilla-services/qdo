# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest2 as unittest
from zktools.node import ZkNode

from qdo import testing
from qdo.tests.base import ZKBase
from qdo.zk import connect as zk_connect


class TestZookeeper(unittest.TestCase, ZKBase):

    @classmethod
    def setUpClass(cls):
        ZKBase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        ZKBase.tearDownClass()

    def setUp(self):
        ZKBase._clean_zk()

    def test_add_node_cluster_visibility(self):
        node_path = u'/node1'
        with zk_connect(u'127.0.0.1:2181,127.0.0.1:2184,'
                '127.0.0.1:2187' + self.zk_root) as conn1:
            ZkNode(conn1, node_path)
            self.assertTrue(conn1.exists(node_path))
        with zk_connect(u'127.0.0.1:2184' + self.zk_root) as conn2:
            self.assertTrue(conn2.exists(node_path))
        with zk_connect(u'127.0.0.1:2187' + self.zk_root) as conn3:
            self.assertTrue(conn3.exists(node_path))

    def test_cluster_connection(self):
        node_path = u'/node2'
        conn1 = self._make_zk_conn()
        node = ZkNode(conn1, node_path)
        node.value = 1
        # shut down the current zk server
        supervisor = testing.processes[u'supervisor']
        try:
            supervisor.stopProcess(u'zookeeper:zk1')
            node.value = 2
            # open a new connection and ensure the value has been set in
            # Zookeeper
            with zk_connect(u'127.0.0.1:2184' + self.zk_root) as conn2:
                self.assertTrue(conn2.exists(node_path))
                node2 = ZkNode(conn2, node_path)
                self.assertEqual(node2.value, 2)
        finally:
            supervisor.startProcess(u'zookeeper:zk1')
