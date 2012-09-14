# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from metlog.holder import get_client
from metlog.senders.dev import DebugCaptureSender


def get_logger():
    """Get a global :term:`metlog` client.

    :rtype: :py:class:`metlog.client.MetlogClient`
    """
    return get_client('qdo-worker')


def configure(settings, debug=False):
    """Configure a :term:`metlog` client and sender, either based on the
    passed in :py:attr:`settings` or as a debug sender.
    """
    if debug:
        debug_config = {'sender': {
            'class': 'metlog.senders.dev.DebugCaptureSender'}}
        get_client('qdo-worker', debug_config)
    else:
        logger = get_client('qdo-worker')
        # don't reconfigure an already configured debug logger
        if not isinstance(logger.sender, DebugCaptureSender):
            get_client('qdo-worker', settings)
