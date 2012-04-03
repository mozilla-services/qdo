# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import contextmanager
from socket import create_connection

from zc.zk import ZooKeeper


@contextmanager
def connect(hosts):
    conn = None
    try:
        conn = ZooKeeper(hosts, wait=True)
        yield conn
    finally:
        if conn is not None:
            conn.close()


def sent_command(host=u'127.0.0.1', port=2181, command=b'ruok'):
    sock = create_connection((host, port))
    sock.sendall(command)
    result = sock.recv(8192)
    sock.close()
    return [l.strip() for l in result.split('\n') if l]
