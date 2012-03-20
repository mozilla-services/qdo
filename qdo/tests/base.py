# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from requests.exceptions import ConnectionError
from ujson import decode as ujson_decode
from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import ZOO_DEFAULT_ROOT
from qdo.queuey import QueueyConnection

# as specified in the queuey-dev.ini
TEST_APP_KEY = u'f25bfb8fe200475c8a0532a9cbe7651e'
connections = {}


class ZKBase(object):

    zk_root = ZOO_DEFAULT_ROOT

    @classmethod
    def setUpClass(cls):
        global connections
        conn = connections.get(u'zk_root', None)
        if conn is None:
            connections[u'zk_root'] = conn = ZooKeeper(
                u'127.0.0.1:2187', wait=True)
        if conn.exists(cls.zk_root):
            conn.delete_recursive(cls.zk_root)
        ZkNode(conn, cls.zk_root)

    @classmethod
    def tearDownClass(cls):
        global connections
        conn = connections.get(u'zk_root', None)
        if conn is not None:
            conn.delete_recursive(cls.zk_root)
            conn.close()
            del connections[u'zk_root']

    @classmethod
    def _make_zk_conn(cls):
        return ZooKeeper(u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187' +
            cls.zk_root, wait=True)

    @classmethod
    def _clean_zk(cls, conn):
        for child in conn.get_children(u'/'):
            conn.delete_recursive(u'/' + child)


class QueueyBase(object):

    @classmethod
    def setUpClass(cls):
        cls._queuey_conn = cls._make_queuey_conn()
        cls._clean_queuey()

    @classmethod
    def tearDownClass(cls):
        del cls._queuey_conn

    @classmethod
    def _make_queuey_conn(cls,
            connection=u'https://127.0.0.1:5001/v1/queuey/'):
        return QueueyConnection(TEST_APP_KEY, connection=connection)

    @classmethod
    def _clean_queuey(cls):
        conn = cls._queuey_conn
        try:
            response = conn.get()
            queues = ujson_decode(response.text)[u'queues']
            names = [q[u'queue_name'] for q in queues]
            for n in names:
                conn.delete(n)
        except ConnectionError:
            pass
