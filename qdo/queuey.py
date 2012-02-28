# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from urlparse import urljoin
from urlparse import urlsplit

import requests

from qdo.utils import metlogger


def retry(retries, method, *args, **kwargs):
    """Retry a given method up to `retries` times on connection timeouts.

    :param retries: Number of retry attempt
    :type retries: int
    :param method: The method to call
    :type method: func
    :param args: Arguments to pass to the method
    :type method: list
    :param kwargs: Keyword arguments to pass to the method
    :type method: dict
    """
    for n in range(retries):
        try:
            response = method(*args, **kwargs)
        except requests.Timeout:
            metlogger.incr('queuey.conn_timeout')
        except requests.ConnectionError:
            metlogger.incr('queuey.conn_error')
            raise
        else:
            return response
    # raise timeout after all
    raise


class QueueyConnection(object):
    """Represents a connection to one :term:`Queuey` server. The connection
    holds on to a connection pool and automatically uses keep alive
    connections.

    :param app_key: The applications key used for authorization
    :type app_key: str
    :param connection: Connection information for the :term:`Queuey` server
    :type connection: str
    """

    #: Number of retries on connection timeouts
    retries = 3
    #: Connection timeout in seconds
    timeout = 2.0

    def __init__(self, app_key,
                 connection='https://127.0.0.1:5001/v1/queuey/'):
        self.app_key = app_key
        self.connection = connection.split(',')
        self.app_url = self.connection[0]
        headers = {'Authorization': 'Application %s' % app_key}
        self.session = requests.session(
            headers=headers, timeout=self.timeout)

    def connect(self):
        """Establish a connection to the :term:`Queuey` heartbeat url, retry
        up to :py:attr:`retries` times on connection timeout.
        """
        parts = urlsplit(self.app_url)
        url = parts.scheme + '://' + parts.netloc + '/__heartbeat__'
        return retry(self.retries, self.session.head, url)

    def get(self, url='', params=None):
        """Perform a GET request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to get, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return retry(self.retries, self.session.get,
            url, params=params, timeout=self.timeout)

    def post(self, url='', params=None, data=''):
        """Perform a POST request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :param data: The body payload, either a string for a single message
            or a JSON dictionary conforming with the :term:`Queuey` API.
        :type data: str
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return retry(self.retries, self.session.post,
            url, params=params, timeout=self.timeout, data=data)

    def delete(self, url='', params=None):
        """Perform a DELETE request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        return retry(self.retries, self.session.delete,
            url, params=params, timeout=self.timeout)
