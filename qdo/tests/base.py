# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from zc.zk import ZooKeeper
from zktools.node import ZkNode

connections = {}


class ZKBase(object):

    @classmethod
    def setUpClass(cls):
        global connections
        if 'zk' not in connections:
            connections['zk'] = conn = ZooKeeper('127.0.0.1:2187', wait=True)
        if conn.exists(u'/test'):
            conn.delete_recursive(u'/test')
        ZkNode(conn, u'/test')

    @classmethod
    def tearDownClass(cls):
        global connections
        if 'zk' in connections:
            conn = connections['zk']
            conn.delete_recursive(u'/test')
            conn.close()
