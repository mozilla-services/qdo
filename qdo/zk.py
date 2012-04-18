# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
from contextlib import contextmanager
from socket import create_connection
import threading

from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import returnValue
from twisted.internet.selectreactor import SelectReactor
from txzookeeper.managed import ManagedClient
import zookeeper

from qdo.config import ZOO_DEFAULT_CONN

ZOO_OPEN_ACL_UNSAFE = dict(
    perms=zookeeper.PERM_ALL, scheme='world', id='anyone')


class ZKReactor(object):

    def __init__(self, servers=ZOO_DEFAULT_CONN):
        self.reactor = SelectReactor()
        self.servers = servers
        self.client = None

    def _poll(self):
        # debugging hook to get into the thread running the twisted loop
        self.reactor.callLater(10, self._poll)

    @inlineCallbacks
    def configure(self):
        self.client = ManagedClient(
            servers=self.servers,
            session_timeout=None)
        yield self.client.connect()
        returnValue(self.client)

    def start(self):
        if self.reactor.running:
            return

        def run_reactor():
            self.reactor.callWhenRunning(self._poll)
            self.reactor.run(installSignalHandlers=0)

        atexit.register(self.stop)
        self.thread = threading.Thread(target=run_reactor)
        self.thread.setDaemon(True)
        self.thread.start()
        self.reactor.callFromThread(self.configure)

    def stop(self):
        if not self.reactor.running:
            return

        if self.client and self.client.connected:
            self.reactor.callFromThread(self.client.close)

        self.reactor.callFromThread(self.reactor.stop)
        self.thread.join(3)
        if self.thread.isAlive():
            # Not dead yet? Well I guess you will have to!
            self.reactor.callFromThread(self.reactor.crash)
            self.thread.join(3)


class ZK(object):

    def __init__(self, hosts):
        self.handle = zookeeper.init(hosts)

    def __getattr__(self, name):
        zoo_func = getattr(zookeeper, name)

        def func(*args, **kwargs):
            return zoo_func(self.handle, *args, **kwargs)
        return func


@contextmanager
def connect(hosts):
    conn = None
    try:
        conn = ZK(hosts)
        yield conn
    finally:
        if conn is not None:
            conn.close()


def create(zk_conn, path, create_mode=0):
    if not zk_conn.exists(path):
        zk_conn.create(path, u'', [ZOO_OPEN_ACL_UNSAFE], create_mode)


def delete_recursive(conn, root):
    for child in conn.get_children(root):
        path = root + u'/' + child
        if conn.get_children(path):
            delete_recursive(conn, path)
        conn.delete(path)
    conn.delete(root)


def sent_command(host=u'127.0.0.1', port=2181, command=b'ruok'):
    sock = create_connection((host, port))
    sock.sendall(command)
    result = sock.recv(8192)
    sock.close()
    return [l.strip() for l in result.split('\n') if l]
