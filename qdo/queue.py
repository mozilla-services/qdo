# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import deque
import json
from urlparse import urljoin

import requests


class QueueyConnection(object):

    def __init__(self, server_url='http://127.0.0.1:5000',
                 application_key=''):
        """Represents a connection to one Queuey server

        :param server_url: Base URL of the Queuey server
        :type server_url: str
        :param application_key: The applications key
        :type application_key: str
        """
        self.server_url = server_url
        self.application_key = application_key
        headers = {'X-Application-Key': application_key}
        self.session = requests.session(headers=headers, timeout=2.0)

    def connect(self):
        """Establish connection to Queuey heartbeat url."""
        return self.session.head(urljoin(self.server_url, '__heartbeat__'))

    def get(self, url, params):
        """Perform an actual get request against Queuey."""
        return self.session.get(
            urljoin(self.server_url, url), params=params, timeout=2.0)


class Queue(object):

    def __init__(self, connection, queue_name=''):
        """Create a queue containing messages

        :param connection: A QueueyConnection object
        :type server_url: object
        :param queue_name: The queue name (a uuid4 hash)
        :type queue_name: str
        """
        self.connection = connection
        self.queue_name = queue_name
        self.queue_get_url = queue_name + '/get_messages'
        self._messages = deque()

    def get(self, since_timestamp=None, limit=100, order='descending',
            partition=1):
        """Returns messages for the queue, by default from newest to oldest.

        :param since_timestamp: All messages newer than this timestamp,
            should be formatted as seconds since epoch in GMT
        :type since_timestamp: int
        :param limit: Only return N number of messages, defaults to 100
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to descending
        :type order: str
        :param partition: A specific partition number to retrieve messages
            from. Defaults to retrieving messages from partition 1.
        :type partition: int
        """
        params = {
            'limit': limit,
            'order': order,
            'partition': partition,
        }
        if since_timestamp is not None:
            params['since_timestamp'] = since_timestamp

        response = self.connection.get(self.queue_get_url, params=params)
        if response.status_code == 200:
            return response.text
        # TODO
        return
