# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import uuid

from ujson import decode
from ujson import encode

from qdo.config import STATUS_PARTITIONS
from qdo.config import STATUS_QUEUE


class Partition(object):
    """Represents a specific partition in a message queue.

    :param queuey_conn: A
        :py:class:`Queuey client <queuey_py.Client>` instance.
    :type queuey_conn: object
    :param name: The queue name (a uuid4 hash) or the combined queue name and
        partition id, separated by a dash.
    :type name: str
    :param msgid: The key of the message in the status queue, holding
        information about the processing state of this partition.
    :type msgid: unicode
    :param worker_id: An id for the current worker process, used for logging.
    :type name: unicode
    """

    def __init__(self, queuey_conn, name, msgid=None, worker_id=''):
        self.queuey_conn = queuey_conn
        self.worker_id = worker_id
        if '-' in name:
            self.name = name
            parts = name.split('-')
            self.queue_name, self.partition = parts[0], int(parts[1])
        else:
            self.name = name + '-1'
            self.queue_name, self.partition = (name, 1)
        # map partition to one in 1 to max status partitions
        self.status_partition = ((self.partition - 1) % STATUS_PARTITIONS) + 1
        self.msgid = msgid
        if msgid is None:
            self.msgid = uuid.uuid1().hex
            self._create_status_message()

    @property
    def _status_url(self):
        sp = unicode(self.status_partition)
        return STATUS_QUEUE + '/' + sp + '%3A' + self.msgid

    def _create_status_message(self):
        return self._update_status_message('')

    def _get_status_message(self):
        response = self.queuey_conn.get(self._status_url)
        messages = decode(response.text)['messages']
        if messages:
            return decode(messages[0]['body'])
        return None

    def _update_status_message(self, value):
        result = self.queuey_conn.put(self._status_url, data=encode(dict(
            partition=self.name, processed=value, last_worker=self.worker_id)),
            headers={'X-TTL': '2592000'},  # thirty days
        )
        return result

    def messages(self, limit=100, order='ascending'):
        """Returns messages for the partition, by default from oldest to
           newest.

        :param limit: Only return N number of messages, defaults to 100
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :raises: :py:exc:`queuey_py.HTTPError`
        :rtype: list
        """
        return self.queuey_conn.messages(self.queue_name,
            partition=self.partition, since=self.last_message, limit=limit,
            order=order)

    @property
    def last_message(self):
        """Property for the message id of the last processed message.
        """
        msg = self._get_status_message()
        if msg is None:
            return ''
        return msg['processed']

    @last_message.setter
    def last_message(self, value):
        """Sets the message id of the last processed message.

        :param value: New message id value.
        :type value: str
        """
        self._update_status_message(value)
