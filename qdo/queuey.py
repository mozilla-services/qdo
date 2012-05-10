# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from functools import wraps
from random import randint
from urlparse import urljoin
from urlparse import urlsplit

from requests import session
from requests.exceptions import ConnectionError
from requests.exceptions import SSLError
from requests.exceptions import Timeout
import ujson
from ujson import decode as ujson_decode

import qdo.exceptions
from qdo.log import get_logger


def retry(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        for n in range(self.retries):
            try:
                return func(self, *args, **kwargs)
            except Timeout:
                get_logger().incr(u'queuey.conn_timeout')
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
                get_logger().incr(u'queuey.conn_ssl_error')
            else:
                get_logger().incr(u'queuey.conn_error')
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
    :param retries: Number of retries on connection timeouts
    :type retries: int
    :param timeout: Connection timeout in seconds
    :type timeout: float
    """

    def __init__(self, app_key,
                 connection=u'https://127.0.0.1:5001/v1/queuey/',
                 retries=3, timeout=2.0):
        self.app_key = app_key
        self.retries = retries
        self.timeout = timeout
        self.connection = [c.strip() for c in connection.split(',')]
        rand_index = randint(0, len(self.connection))
        self.app_url = self.connection[rand_index - 1]
        self.fallback_urls = self.connection[:(rand_index - 1)] + \
            self.connection[rand_index:]
        self.failed_urls = []
        headers = {u'Authorization': u'Application %s' % app_key}
        # Setting pool_maxsize to 1 ensures we re-use the same connection.
        # requests/urllib3 will always create maxsize connections and then
        # cycle through them one after the other
        self.session = session(headers=headers, timeout=self.timeout,
            config={u'pool_maxsize': 1, u'keep_alive': True}, prefetch=True)
        self.timer = get_logger().timer

    @fallback
    @retry
    def connect(self):
        """Establish a connection to the :term:`Queuey` heartbeat url, retry
        up to :py:attr:`retries` times on connection timeout.
        """
        parts = urlsplit(self.app_url)
        url = parts.scheme + u'://' + parts.netloc + u'/__heartbeat__'
        return self.session.head(url)

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
            params=params, timeout=self.timeout)

    @fallback
    @retry
    def post(self, url='', params=None, data='', headers=None):
        """Perform a POST request against :term:`Queuey`, retry
        up to :py:attr:`retries` times on connection timeout.

        :param url: Relative URL to post to, without a leading slash.
        :type url: str
        :param params: Additional query string parameters.
        :type params: dict
        :param data: The body payload, either a string for a single message
            or a list of strings for posting multiple messages or a dict
            for form encoded values.
        :type data: str
        :param headers: Additional request headers.
        :type headers: dict
        :rtype: :py:class:`requests.models.Response`
        """
        url = urljoin(self.app_url, url)
        if isinstance(data, list):
            # support message batches
            messages = []
            for d in data:
                messages.append({u'body': d, u'ttl': 3600})
            data = ujson.encode({u'messages': messages})
            headers = {u'content-type': u'application/json'}
        return self.session.post(url, headers=headers,
            params=params, timeout=self.timeout, data=data)

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
            params=params, timeout=self.timeout)

    def _create_queue(self, partitions=1, queue_name=None):
        # helper method to create a new queue and return its name
        data = {u'partitions': partitions}
        if queue_name is not None:
            data[u'queue_name'] = queue_name
        response = self.post(data=data)
        return ujson.decode(response.text)[u'queue_name']

    def _messages(self, queue_name, partition=1, since=0.0, limit=100,
                  order='ascending'):
        params = {
            u'limit': limit,
            u'order': order,
            u'partitions': partition,
        }
        if since:
            # use the repr, to avoid a float getting clobbered by implicit
            # str() calls in the URL generation
            params[u'since'] = repr(since)
        with self.timer(u'queuey.get_messages'):
            response = self.get(queue_name, params=params)
        if response.ok:
            messages = ujson_decode(response.text)[u'messages']
            # filter out exact timestamp matches
            return [m for m in messages if float(str(m[u'timestamp'])) > since]
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)

    def _partitions(self):
        # Prototype for listing all partitions, in the final code partition
        # names will be taken from ZK under /partitions
        # A helper method to populate ZK from Queuey might be nice
        with get_logger().timer(u'queuey.get_partitions'):
            response = self.get(params={u'details': True})
        queues = ujson.decode(response.text)[u'queues']
        partitions = []
        for q in queues:
            name = q[u'queue_name']
            part = q[u'partitions']
            for i in xrange(1, part + 1):
                partitions.append(u'%s-%s' % (name, i))
        return partitions
