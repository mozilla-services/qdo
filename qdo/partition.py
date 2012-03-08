# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import ujson

import qdo.exceptions


class Partition(object):
    """Represents a specific partition in a message queue.

    :param queuey_conn: A
        :py:class:`QueueyConnection <qdo.queue.QueueyConnection>` instance
    :type server_url: object
    :param zk_conn: A :term:`Zookeeper` connection
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

    def get(self, since=None, limit=100, order='ascending'):
        """Returns messages for the partition, by default from oldest to
           newest.

        :param since: All messages newer than this time stamp or message id,
            should be formatted as seconds since epoch in GMT.
        :type since: str
        :param limit: Only return N number of messages, defaults to 100
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :raises: :py:exc:`qdo.exceptions.HTTPError`
        :rtype: dict
        """
        params = {
            'limit': limit,
            'order': order,
            'partitions': self.partition,
        }
        if since is not None:
            # use the repr, to avoid a float getting clobbered by implicit
            # str() calls in the URL generation
            params['since'] = repr(since)

        response = self.queuey_conn.get(self.queue_name, params=params)
        if response.ok:
            return ujson.decode(response.text)
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)
