# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ujson
from zktools.node import ZkNode

import qdo.exceptions
from qdo.log import get_logger


class Partition(object):
    """Represents a specific partition in a message queue.

    :param queuey_conn: A
        :py:class:`QueueyConnection <qdo.queue.QueueyConnection>` instance.
    :type queuey_conn: object
    :param zk_conn: A :term:`Zookeeper` connection instance.
    :type zk_conn: object
    :param name: The queue name (a uuid4 hash) or the combined queue name and
        partition id, separated by a dash.
    :type name: str
    """

    def __init__(self, queuey_conn, zk_conn, name):
        self.queuey_conn = queuey_conn
        self.zk_conn = zk_conn
        if '-' in name:
            self.name = name
            self.queue_name, self.partition = name.split(u'-')
        else:
            self.name = name + u'-1'
            self.queue_name, self.partition = (name, 1)

        self.zk_node = ZkNode(zk_conn, u'/partitions/' + name, use_json=True)
        if self.zk_node.value is None:
            self.zk_node.value = 0.0
        self.timer = get_logger().timer

    def messages(self, limit=100, order='ascending'):
        """Returns messages for the partition, by default from oldest to
           newest.

        :param limit: Only return N number of messages, defaults to 100
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :raises: :py:exc:`qdo.exceptions.HTTPError`
        :rtype: list
        """
        since = self.timestamp
        params = {
            u'limit': limit,
            u'order': order,
            u'partitions': self.partition,
            # use the repr, to avoid a float getting clobbered by implicit
            # str() calls in the URL generation
            u'since': repr(since),
        }
        with self.timer(u'queuey.get_messages'):
            response = self.queuey_conn.get(self.queue_name, params=params)
        if response.ok:
            messages = ujson.decode(response.text)[u'messages']
            # filter out exact timestamp matches
            return [m for m in messages if float(str(m[u'timestamp'])) > since]
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)

    @property
    def timestamp(self):
        """Property for the timestamp of the last processed message.
        """
        with self.timer(u'zookeeper.get_value'):
            return float(self.zk_node.value)

    @timestamp.setter
    def timestamp(self, value):
        """Sets the timestamp of the last processed message.

        :param value: New timestamp value as a float.
        :type value: float
        """
        with self.timer(u'zookeeper.set_value'):
            if isinstance(value, basestring):
                value = float(str(value))
            self.zk_node.value = repr(value)
