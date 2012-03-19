# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import unittest2 as unittest

from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo import testing
from qdo.tests.base import ZKBase


class TestZookeeper(unittest.TestCase, ZKBase):

    @classmethod
    def setUpClass(cls):
        ZKBase.setUpClass()
        cls.zk_conn = cls._make_zk_conn()
        cls.supervisor = testing.processes[u'supervisor']

    @classmethod
    def tearDownClass(cls):
        cls.zk_conn.close()
        ZKBase.tearDownClass()

    def setUp(self):
        ZKBase._clean_zk(self.zk_conn)

    def tearDown(self):
        self.supervisor.startProcessGroup(u'zookeeper')

    def test_add_node_cluster_visibility(self):
        node_path = u'/node1'
        ZkNode(self.zk_conn, node_path)
        conn2 = ZooKeeper(u'127.0.0.1:2184' + self.zk_root, wait=True)
        self.assertTrue(conn2.exists(node_path))
        conn2.close()
        conn3 = ZooKeeper(u'127.0.0.1:2187' + self.zk_root, wait=True)
        self.assertTrue(conn3.exists(node_path))
        conn3.close()

    def test_cluster_connection(self):
        conn = self.zk_conn
        node_path = u'/node2'
        node = ZkNode(conn, node_path)
        node.value = 1
        # shut down the current zk server
        self.supervisor.stopProcess(u'zookeeper:zk1')
        node.value = 2
        # open a new connection and ensure the value has been set in
        # Zookeeper
        conn2 = ZooKeeper(u'127.0.0.1:2184' + self.zk_root, wait=True)
        self.assertTrue(conn2.exists(node_path))
        node2 = ZkNode(conn2, node_path)
        self.assertEqual(node2.value, 2)
        conn2.close()
