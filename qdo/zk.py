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
from twisted.internet import reactor
from twisted.internet.threads import blockingCallFromThread
from txzookeeper.managed import ManagedClient
import zookeeper

from qdo.config import ZOO_DEFAULT_CONN

ZOO_OPEN_ACL_UNSAFE = dict(
    perms=zookeeper.PERM_ALL, scheme='world', id='anyone')


class ZKReactor(object):
    """Zookeeper connection handling, based on `txzookeeper` and Twisted,
    while hiding most of the asynchronous nature of those.

    The Twisted reactor is a module global. The API is limited to one
    `ZKReactor` instance per process.

    :param connection: Zookeeper connection string
    :type connection: unicode
    :param session_timeout: Zookeeper session timeout hint in milliseconds
    :type session_timeout: int
    """

    # make global reactor available for convenience
    reactor = reactor

    def __init__(self, connection=ZOO_DEFAULT_CONN, session_timeout=5000):
        self.connection = connection
        self.session_timeout = session_timeout
        self.client = None
        self.thread = None

    def start(self):
        if self.reactor.running:
            self.connect()
            return

        def run_reactor():
            # signal handlers only work in the main thread
            self.reactor.run(installSignalHandlers=False)

        atexit.register(self.stop)
        self.thread = threading.Thread(target=run_reactor)
        self.thread.setDaemon(True)
        self.thread.start()
        self.connect()

    def stop(self):
        if not self.reactor.running:
            return

        self.close()
        if not self.reactor.running:
            self.call(self.reactor.stop)
        if self.thread is not None:
            self.thread.join(3)
            if self.thread.isAlive():
                # Not dead yet? Force!
                self.call(self.reactor.crash)
                self.thread.join(3)

    def connect(self):
        if self.client is None:
            self.blocking_call(self.configure)
        elif not self.client.connected:
            self.blocking_call(self.client.connect)

    def close(self):
        if self.client is not None and self.client.connected:
            self.blocking_call(self.client.close)
        self.client = None

    @inlineCallbacks
    def configure(self):
        self.client = ManagedClient(
            servers=self.connection,
            session_timeout=self.session_timeout)
        yield self.client.connect()
        # ensure global state is present
        yield self._create(u'/workers')
        yield self._create(u'/partitions')
        yield self._create(u'/partition-owners')
        returnValue(self.client)

    def call(self, func, *args, **kw):
        return self.reactor.callFromThread(func, *args, **kw)

    def blocking_call(self, func, *args, **kw):
        return blockingCallFromThread(self.reactor, func, *args, **kw)

    def create(self, path, data=u'', flags=0):
        self.blocking_call(self._create, path, flags=flags)

    @inlineCallbacks
    def _create(self, path, data=u'', flags=0):
        try:
            yield self.client.create(path, data=data, flags=flags)
        except zookeeper.NodeExistsException:
            pass

    def delete(self, path, version=-1):
        self.blocking_call(self._delete, path, version=version)

    @inlineCallbacks
    def _delete(self, path, version=-1):
        yield self.client.delete(path, version=version)

    def exists(self, path):
        return self.blocking_call(self.client.exists, path)

    def get(self, path):
        return self.blocking_call(self.client.get, path)

    def get_children(self, path):
        return self.blocking_call(self.client.get_children, path)

    def set(self, path, data=u'', version=-1):
        self.blocking_call(self.client.set, path, data=data, version=version)


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


def send_command(host=u'127.0.0.1', port=2181, command=b'ruok'):
    sock = create_connection((host, port))
    sock.sendall(command)
    result = sock.recv(8192)
    sock.close()
    return [l.strip() for l in result.split('\n') if l]
