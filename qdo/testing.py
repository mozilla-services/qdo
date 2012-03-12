# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import ZOO_DEFAULT_NS


def cleanup_zookeeper():
    """Opens a connection to Zookeeper and removes all nodes from it."""
    root = '/' + ZOO_DEFAULT_NS
    zk_conn = ZooKeeper('127.0.0.1:2181', wait=True)
    if zk_conn.exists(root):
        zk_conn.delete_recursive(root)
    ZkNode(zk_conn, root)
    zk_conn.close()


def setup():
    """Shared one-time test setup."""
    cleanup_zookeeper()


def teardown():
    """Shared one-time test tear down."""
    cleanup_zookeeper()
