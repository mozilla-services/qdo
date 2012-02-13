# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import deque


class Queue(object):

    def __init__(self, server_url=''):
        """Create a queue containing messages

        :param server_url: Base URL of the Queuey server
        :type server_url: str
        """
        self.server_url = server_url
        self._messages = deque()

    def pop(self):
        """Pop one message from the queue."""
        message = self._messages.popleft()
        return message

    def _add(self, message):
        """Internal testing API to directly add messages to the queue."""
        self._messages.append(message)
