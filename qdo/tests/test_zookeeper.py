# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest2 as unittest
from zktools.node import ZkNode

from qdo import testing
from qdo.tests.base import ZKBase


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
        conn1 = self._make_zk_conn()
        ZkNode(conn1, node_path)
        conn1.close()
        conn2 = self._make_zk_conn(hosts=u'127.0.0.1:2184')
        self.assertTrue(conn2.exists(node_path))
        conn2.close()
        conn3 = self._make_zk_conn(hosts=u'127.0.0.1:2187')
        self.assertTrue(conn3.exists(node_path))
        conn3.close()

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
            conn2 = self._make_zk_conn(hosts=u'127.0.0.1:2184')
            self.assertTrue(conn2.exists(node_path))
            node2 = ZkNode(conn2, node_path)
            self.assertEqual(node2.value, 2)
            conn2.close()
        finally:
            supervisor.startProcess(u'zookeeper:zk1')
