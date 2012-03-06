# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import wraps
from urlparse import urljoin
from urlparse import urlsplit

from requests import session
from requests.exceptions import ConnectionError
from requests.exceptions import SSLError
from requests.exceptions import Timeout
import ujson

from qdo.utils import metlogger


def retry(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        for n in range(self.retries):
            try:
                return func(self, *args, **kwargs)
            except Timeout:
                metlogger.incr('queuey.conn_timeout')
        # raise timeout after all
        raise
    return wrapped


def fallback(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (SSLError, ConnectionError) as e:
            if isinstance(e, SSLError):
                metlogger.incr('queuey.conn_ssl_error')
            else:
                metlogger.incr('queuey.conn_error')
            if self.fallback_urls:
                self.failed_urls.append(self.app_url)
                self.app_url = self.fallback_urls.pop()
                return func(self, *args, **kwargs)
            # raise connection error after all
            raise
    return wrapped


class QueueyConnection(object):
    """Represents a connection to one :term:`Queuey` server.

    :param app_key: The applications key used for authorization
    :type app_key: str
    :param connection: Connection information for the Queuey server.
        Either a single full URL to the Queuey app or multiple comma
        separated URLs.
    :type connection: str
    """

    #: Number of retries on connection timeouts
    retries = 3
    #: Connection timeout in seconds
    timeout = 2.0

    def __init__(self, app_key,
                 connection='https://127.0.0.1:5001/v1/queuey/'):
        self.app_key = app_key
        self.connection = [c.strip() for c in connection.split(',')]
        self.app_url = self.connection[0]
        self.fallback_urls = self.connection[1:]
        self.failed_urls = []
        headers = {'Authorization': 'Application %s' % app_key}
        # setting pool_maxsize to 1 ensures we re-use the same connection
        # requests/urllib3 will always create maxsize connections and then
        # cycle through them one after the other. internally it's a queue
        self.session = session(headers=headers, timeout=self.timeout,
            config={'pool_maxsize': 1, 'keep_alive': True})

    @fallback
    @retry
    def connect(self):
        """Establish a connection to the :term:`Queuey` heartbeat url, retry
        up to :py:attr:`retries` times on connection timeout.
        """
        parts = urlsplit(self.app_url)
        url = parts.scheme + '://' + parts.netloc + '/__heartbeat__'
        return self.session.head(url, prefetch=True)

    @fallback
    @retry
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
        return self.session.get(url,
            params=params, timeout=self.timeout, prefetch=True)

    @fallback
    @retry
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
        return self.session.post(url,
            params=params, timeout=self.timeout, data=data, prefetch=True)

    @fallback
    @retry
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
        return self.session.delete(url,
            params=params, timeout=self.timeout, prefetch=True)

    def _create_queue(self):
        # helper method to create a new queue and return its name
        response = self.post()
        return ujson.decode(response.text)[u'queue_name']
