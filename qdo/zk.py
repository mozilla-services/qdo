# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import atexit
from contextlib import contextmanager
from socket import create_connection
import threading

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.selectreactor import SelectReactor
from txzookeeper.client import ZookeeperClient
import zookeeper


class ZKReactor(object):

    def __init__(self, poll_interval=1):
        self.reactor = SelectReactor()
        self.poll_interval = poll_interval
        self.client = None

    @inlineCallbacks
    def configure(self):
        self.client = yield ZookeeperClient(
            servers=u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187'
                '/mozilla-qdo',
            session_timeout=None).connect()
        returnValue(self.client)

    def start(self):
        if self.reactor.running:
            return

        def run_reactor():
            self.reactor.callWhenRunning(self.poll)
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

    def poll(self):
        self.reactor.callLater(self.poll_interval, self.poll)


class ZK(object):

    def __init__(self, handle):
        self._handle = handle

    def __getattr__(self, name):
        zoo_func = getattr(zookeeper, name)

        def func(*args, **kwargs):
            return zoo_func(self._handle, *args, **kwargs)
        return func


@contextmanager
def connect(hosts):
    handle = None
    try:
        handle = zookeeper.init(hosts)
        yield ZK(handle)
    finally:
        if handle is not None:
            zookeeper.close(handle)


def sent_command(host=u'127.0.0.1', port=2181, command=b'ruok'):
    sock = create_connection((host, port))
    sock.sendall(command)
    result = sock.recv(8192)
    sock.close()
    return [l.strip() for l in result.split('\n') if l]
