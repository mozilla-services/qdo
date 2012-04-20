# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import time

from requests.exceptions import ConnectionError
from ujson import decode as ujson_decode
from unittest2 import TestCase
import zookeeper

from qdo.config import ZOO_DEFAULT_HOST
from qdo.config import ZOO_DEFAULT_ROOT
from qdo.queuey import QueueyConnection
from qdo import zk

# as specified in the queuey.ini
TEST_APP_KEY = u'f25bfb8fe200475c8a0532a9cbe7651e'


class ZKBase(object):

    zk_root = ZOO_DEFAULT_ROOT

    @classmethod
    def setUpClass(cls):
        zookeeper.set_debug_level(zookeeper.LOG_LEVEL_ERROR)
        with zk.connect(u'127.0.0.1:2181') as root_conn:
            zk.create(root_conn, cls.zk_root)
        cls._zk_conn = cls._make_zk_conn()

    @classmethod
    def tearDownClass(cls):
        cls._clean_zk()
        cls._zk_conn.close()
        del cls._zk_conn
        zookeeper.set_debug_level(zookeeper.LOG_LEVEL_DEBUG)

    @classmethod
    def _make_zk_conn(cls, hosts=ZOO_DEFAULT_HOST):
        return zk.ZK(hosts + cls.zk_root)

    @classmethod
    def _make_zk_reactor(cls):
        reactor = zk.ZKReactor()
        reactor.start()
        return reactor

    @classmethod
    def _clean_zk(cls, count=0):
        if count > 10:
            raise ValueError(u"Couldn't clean up Zookeeper")
        conn = cls._zk_conn
        for child in conn.get_children(u'/'):
            zk.delete_recursive(conn, u'/' + child)
        if len(conn.get_children(u'/')) > 0:
            time.sleep(0.5)
            cls._clean_zk(count + 1)


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


class BaseTestCase(TestCase, QueueyBase, ZKBase):

    @classmethod
    def setUpClass(cls):
        ZKBase.setUpClass()
        QueueyBase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        ZKBase.tearDownClass()
        QueueyBase.tearDownClass()

    def setUp(self):
        QueueyBase._clean_queuey()
        ZKBase._clean_zk()
