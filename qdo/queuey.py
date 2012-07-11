# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from queuey_py import Client
from ujson import decode as ujson_decode

import qdo.exceptions


class QueueyConnection(Client):

    def messages(self, queue_name, partition=1, since=0.0, limit=100,
                  order='ascending'):
        """Returns messages for a queue, by default from oldest to
           newest.

        :param queue_name: Queue name
        :type queue_name: unicode
        :param partition: Partition number, defaults to 1.
        :type partition: int
        :param since: Only return messages since a given timestamp, defaults
            to no restriction.
        :type since: float
        :param limit: Only return N number of messages, defaults to 100.
        :type limit: int
        :param order: 'descending' or 'ascending', defaults to ascending
        :type order: str
        :raises: :py:exc:`qdo.exceptions.HTTPError`
        :rtype: list
        """
        params = {
            u'limit': limit,
            u'order': order,
            u'partitions': partition,
        }
        if since:
            # use the repr, to avoid a float getting clobbered by implicit
            # str() calls in the URL generation
            params[u'since'] = repr(since)
        response = self.get(queue_name, params=params)
        if response.ok:
            messages = ujson_decode(response.text)[u'messages']
            # filter out exact timestamp matches
            return [m for m in messages if float(str(m[u'timestamp'])) > since]
        # failure
        raise qdo.exceptions.HTTPError(response.status_code, response)
