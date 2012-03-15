# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import time
import xmlrpclib

import pycassa
from zc.zk import ZooKeeper
from zktools.node import ZkNode

from qdo.config import ZOO_DEFAULT_NS

processes = {}


def live_job(message):
    body = message[u'body']
    if body == u'stop':
       raise KeyboardInterrupt
    elif body == u'wait':
        time.sleep(0.01)


def cleanup_zookeeper():
    """Opens a connection to Zookeeper and removes all nodes from it."""
    root = '/' + ZOO_DEFAULT_NS
    zk_conn = ZooKeeper('127.0.0.1:2187', wait=True)
    if zk_conn.exists(root):
        zk_conn.delete_recursive(root)
    ZkNode(zk_conn, root)
    zk_conn.close()


def setup_cassandra_schema():
    hosts = ['127.0.0.1:9160']
    while 1:
        try:
            pycassa.ConnectionPool(keyspace='MessageStore', server_list=hosts)
            break
        except pycassa.InvalidRequestException as e:
            if 'Keyspace MessageStore does not exist' in e.why:
                lhost = hosts[0].split(':')[0]
                os.system('bin/cassandra/bin/cassandra-cli -host %s --file etc/cassandra/message_schema.txt' % lhost)
                os.system('bin/cassandra/bin/cassandra-cli -host %s --file etc/cassandra/metadata_schema.txt' % lhost)
            break
        except pycassa.AllServersUnavailable:
            time.sleep(1)


def ensure_process(name, timeout=10):
    srpc = processes['supervisor']
    if srpc.getProcessInfo(name)['statename'] in ('STOPPED', 'EXITED'):
        print(u'Starting %s!\n' % name)
        srpc.startProcess(name)
    # wait for startup to succeed
    for i in xrange(1, timeout):
        state = srpc.getProcessInfo(name)['statename']
        if state == 'RUNNING':
            break
        elif state != 'RUNNING':
            print(u'Waiting on %s for %s seconds.' % (name, i * 0.1))
            time.sleep(i * 0.1)
    if srpc.getProcessInfo(name)['statename'] != 'RUNNING':
        raise RuntimeError('%s not running' % name)


def setup_supervisor():
    processes['supervisor'] = xmlrpclib.ServerProxy(
        'http://127.0.0.1:4999').supervisor


def setup():
    """Shared one-time test setup, called from tests/__init__.py"""
    setup_supervisor()
    ensure_process('cassandra')
    setup_cassandra_schema()
    ensure_process('zookeeper:zk1')
    ensure_process('zookeeper:zk2')
    ensure_process('zookeeper:zk3')
    cleanup_zookeeper()
    ensure_process('queuey')
    ensure_process('nginx')


def teardown():
    """Shared one-time test tear down, called from tests/__init__.py"""
    cleanup_zookeeper()
