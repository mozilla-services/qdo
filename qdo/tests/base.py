# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import ZOO_DEFAULT_NS

connections = {}


class ZKBase(object):

    zk_root = u'/' + ZOO_DEFAULT_NS

    @classmethod
    def setUpClass(cls):
        global connections
        if 'zk' not in connections:
            connections['zk'] = conn = ZooKeeper('127.0.0.1:2187', wait=True)
        if conn.exists(cls.zk_root):
            conn.delete_recursive(cls.zk_root)
        ZkNode(conn, cls.zk_root)

    @classmethod
    def tearDownClass(cls):
        global connections
        if 'zk' in connections:
            conn = connections['zk']
            conn.delete_recursive(cls.zk_root)
            conn.close()
