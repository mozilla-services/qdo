# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from urllib import quote_plus
import uuid

from ujson import decode
from ujson import encode

from qdo.config import STATUS_QUEUE
from qdo.log import get_logger


class Partition(object):
    """Represents a specific partition in a message queue.

    :param queuey_conn: A
        :py:class:`QueueyConnection <qdo.queue.QueueyConnection>` instance.
    :type queuey_conn: object
    :param name: The queue name (a uuid4 hash) or the combined queue name and
        partition id, separated by a dash.
    :type name: str
    :param msgid: The key of the message in the status queue, holding
        information about the processing state of this partition.
    :type msgid: unicode
    """

    def __init__(self, queuey_conn, name, msgid=None):
        self.queuey_conn = queuey_conn
        if '-' in name:
            self.name = name
            self.queue_name, self.partition = name.split(u'-')
        else:
            self.name = name + u'-1'
            self.queue_name, self.partition = (name, 1)
        self.timer = get_logger().timer
        self.msgid = msgid
        if msgid is None:
            self.msgid = uuid.uuid1().hex
            self._create_status_message()

    def _create_status_message(self):
        return self._update_status_message(u'0.0')

    def _get_status_message(self):
        # XXX add new API to Queuey to get one explicit message id, instead
        # of hoping to have it included inside the last 100 messages
        messages = self.queuey_conn.messages(STATUS_QUEUE, order=u'descending')
        for msg in messages:
            if msg[u'message_id'] == self.msgid:
                return decode(msg[u'body'])
        return None

    def _update_status_message(self, value):
        q = STATUS_QUEUE + u'/' + quote_plus(u'1:' + self.msgid)
        result = self.queuey_conn.put(q, data=encode(dict(
            partition=self.name, processed=value, last_worker=u'')),
            # XXX increase ttl after queuey allows for more
            # https://github.com/mozilla-services/queuey/issues/4
            headers={u'X-TTL': u'259200'},  # three days
            )
        return result

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
        return self.queuey_conn.messages(self.queue_name,
            partition=self.partition, since=self.timestamp, limit=limit,
            order=order)

    @property
    def timestamp(self):
        """Property for the timestamp of the last processed message.
        """
        msg = self._get_status_message()
        if msg is None:
            return 0.0
        return float(msg[u'processed'])

    @timestamp.setter
    def timestamp(self, value):
        """Sets the timestamp of the last processed message.

        :param value: New timestamp value as a float.
        :type value: float
        """
        if isinstance(value, basestring):
            value = float(str(value))
        self._update_status_message(repr(value))
