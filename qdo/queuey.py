# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from urlparse import urljoin

import requests

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
            except requests.Timeout:
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
