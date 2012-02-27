# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json

import qdo.exceptions


class Queue(object):
    """Represents a queue containing messages.

    :param connection: A
        :py:class:`QueueyConnection <qdo.queue.QueueyConnection>` instance
    :type server_url: object
    :param queue_name: The queue name (a uuid4 hash)
    :type queue_name: str
    """

    def __init__(self, connection, queue_name):
        self.connection = connection
        self.queue_name = queue_name

    def get(self, since=None, limit=100, order='ascending', partitions=1):
        """Returns messages for the queue, by default from oldest to newest.

        :param since: All messages newer than this timestamp or message id,
            should be formatted as seconds since epoch in GMT, or the
            hexadecimal message ID
        :type since: str
        :param limit: Only return N number of messages, defaults to 100
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :param partitions: A specific partition number to retrieve messages
            from or a comma separated list of partitions. Defaults to
            retrieving messages from partition 1.
        :type partitions: str
        :raises: :py:exc:`qdo.exceptions.HTTPError`
        :rtype: dict
        """
        params = {
            'limit': limit,
            'order': order,
            'partitions': partitions,
        }
        if since is not None:
            params['since'] = since

        response = self.connection.get(self.queue_name, params=params)
        if response.ok:
            return json.loads(response.text)
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)
