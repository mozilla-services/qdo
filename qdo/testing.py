# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import xmlrpclib

from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import ZOO_DEFAULT_NS

processes = {}


def cleanup_zookeeper():
    """Opens a connection to Zookeeper and removes all nodes from it."""
    root = '/' + ZOO_DEFAULT_NS
    zk_conn = ZooKeeper('127.0.0.1:2181', wait=True)
    if zk_conn.exists(root):
        zk_conn.delete_recursive(root)
    ZkNode(zk_conn, root)
    zk_conn.close()


def ensure_process(name):
    srpc = processes['supervisor']
    if srpc.getProcessInfo(name)['statename'] != 'RUNNING':
        print(u'Starting %s!\n' % name)
        srpc.startProcess(name)
    if srpc.getProcessInfo(name)['statename'] != 'RUNNING':
        raise RuntimeError('%s not running' % name)


def setup_supervisor():
    processes['supervisor'] = xmlrpclib.ServerProxy(
        'http://127.0.0.1:4999').supervisor


def setup():
    """Shared one-time test setup."""
    setup_supervisor()
    ensure_process('zookeeper')
    cleanup_zookeeper()


def teardown():
    """Shared one-time test tear down."""
    cleanup_zookeeper()
