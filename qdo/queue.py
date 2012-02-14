# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import deque


class QueueyConnection(object):

    def __init__(self, server_url='', application_key=''):
        """Represents a connection to one Queuey server

        :param server_url: Base URL of the Queuey server
        :type server_url: str
        :param application_key: The applications key
        :type application_key: str
        """
        self.server_url = server_url
        self.application_key = application_key


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
        self._messages = deque()

    def pop(self):
        """Pop one message from the queue."""
        message = self._messages.popleft()
        return message

    def _add(self, message):
        """Internal testing API to directly add messages to the queue."""
        self._messages.append(message)
