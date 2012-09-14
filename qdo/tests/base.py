# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from queuey_py import Client
from requests.exceptions import ConnectionError
from ujson import decode as ujson_decode
from unittest2 import TestCase

# as specified in the queuey.ini
TEST_APP_KEY = 'f25bfb8fe200475c8a0532a9cbe7651e'


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
            connection='http://127.0.0.1:5000/v1/queuey/'):
        return Client(cls.queuey_app_key, connection=connection)

    @classmethod
    def _clean_queuey(cls):
        conn = cls._queuey_conn
        try:
            response = conn.get()
            queues = ujson_decode(response.text)['queues']
            names = [q['queue_name'] for q in queues]
            for n in names:
                conn.delete(n)
        except ConnectionError:
            pass


class BaseTestCase(TestCase, QueueyBase):

    @classmethod
    def setUpClass(cls):
        QueueyBase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        QueueyBase.tearDownClass()

    def setUp(self):
        QueueyBase._clean_queuey()
