# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from urlparse import urljoin

import requests


class QueueyConnection(object):

    timeout = 2.0

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
        self.base_url = self.server_url + '/queuey/'
        headers = {'Authorization': 'Application %s' % application_key}
        self.session = requests.session(
            headers=headers, timeout=self.timeout)

    def connect(self):
        """Establish connection to Queuey heartbeat url."""
        return self.session.head(urljoin(self.server_url, '__heartbeat__'))

    def get(self, url='', params=None):
        """Perform an actual GET request against Queuey."""
        return self.session.get(urljoin(self.base_url, url),
            params=params, timeout=self.timeout)

    def post(self, url='', params=None, data=''):
        """Perform an actual POST request against Queuey."""
        return self.session.post(urljoin(self.base_url, url),
            params=params, timeout=self.timeout, data=data)


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

    def get(self, since=None, limit=100, order='ascending', partitions=1):
        """Returns messages for the queue, by default from newest to oldest.

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
        """
        params = {
            'limit': limit,
            'order': order,
            'partitions': partitions,
        }
        if since is not None:
            params['since'] = since

        response = self.connection.get(self.queue_name, params=params)
        if response.status_code == 200:
            return response.text
        # failure
        return response.raise_for_status()
