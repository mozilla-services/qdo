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


class ZKBase(object):

    zk_root = ZOO_DEFAULT_ROOT

    @classmethod
    def setUpClass(cls):
        root_conn = ZooKeeper(u'127.0.0.1:2181', wait=True)
        if not root_conn.exists(cls.zk_root):
            ZkNode(root_conn, cls.zk_root)
        root_conn.close()
        cls._zk_conn = cls._make_zk_conn()

    @classmethod
    def tearDownClass(cls):
        cls._clean_zk()
        cls._zk_conn.close()
        del cls._zk_conn

    @classmethod
    def _make_zk_conn(cls,
            hosts=u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187'):
        return ZooKeeper(hosts + cls.zk_root, wait=True)

    @classmethod
    def _clean_zk(cls):
        conn = cls._zk_conn
        for child in conn.get_children(u'/'):
            conn.delete_recursive(u'/' + child)


class QueueyBase(object):

    queuey_app_key = TEST_APP_KEY

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
        return QueueyConnection(cls.queuey_app_key, connection=connection)

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
