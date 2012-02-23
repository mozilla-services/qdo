# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import json
from urlparse import urljoin

import requests

import qdo.exceptions
from qdo.utils import metlogger


class QueueyConnection(object):
    """Represents a connection to one :term:`Queuey` server. The connection
    holds on to a connection pool and automatically uses keep alive
    connections.

    :param server_url: Base URL of the :term:`Queuey` server
    :type server_url: str
    :param application_key: The applications key used for authorization
    :type application_key: str
    """

    #: Number of retries on connection timeouts
    retries = 3
    #: Connection timeout in seconds
    timeout = 2.0
    #: Queuey protocol version
    protocol = 'v1'

    def __init__(self, server_url='http://127.0.0.1:5000',
                 application_name='queuey', application_key=''):
        self.server_url = server_url
        self.application_name = application_name
        self.application_key = application_key
        self.base_url = '%s/%s/%s/' % (
            self.server_url, self.protocol, application_name)
        headers = {'Authorization': 'Application %s' % application_key}
        self.session = requests.session(
            headers=headers, timeout=self.timeout)

    def connect(self):
        """Establish a connection to the :term:`Queuey` heartbeat url, retry
        up to :py:attr:`retries` times on connection timeout.
        """
        url = urljoin(self.server_url, '__heartbeat__')
        for n in range(self.retries):
            try:
                response = self.session.head(url)
            except requests.Timeout, e:
                metlogger.incr('queuey.conn_timeout')
            else:
                return response
        # raise timeout after all
        raise

    def get(self, url='', params=None):
        """Perform a GET request against :term:`Queuey`.

        :param url: Relative URL to get, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :rtype: :py:class:`requests.models.Response`
        """
        return self.session.get(urljoin(self.base_url, url),
            params=params, timeout=self.timeout)

    def post(self, url='', params=None, data=''):
        """Perform a POST request against :term:`Queuey`.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :param data: The body payload, either a string for a single message
            or a JSON dictionary conforming with the :term:`Queuey` API.
        :type params: str
        :rtype: :py:class:`requests.models.Response`
        """
        return self.session.post(urljoin(self.base_url, url),
            params=params, timeout=self.timeout, data=data)


class Queue(object):
    """Represents a queue containing messages.

    :param connection: A
        :py:class:`QueueyConnection <qdo.queue.QueueyConnection>` instance
    :type server_url: object
    :param queue_name: The queue name (a uuid4 hash)
    :type queue_name: str
    """

    def __init__(self, connection, queue_name=''):
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
        :raises: :py:exc:`qdo.exceptions.HTTPError`
        :rtype: unicode
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
            return response.text
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)
