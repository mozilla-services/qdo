# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from contextlib import contextmanager

from zc.zk import ZooKeeper


@contextmanager
def connect(hosts):
    try:
        conn = ZooKeeper(hosts, wait=True)
        yield conn
    finally:
        conn.close()
