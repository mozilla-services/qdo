# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from metlog.config import client_from_dict_config
from metlog.client import MetlogClient
from metlog.senders import DebugCaptureSender

_metlogger = None


def get_logger():
    """Get a global :term:`metlog` client.

    :rtype: :py:class:`metlog.client.MetlogClient`
    """
    global _metlogger
    return _metlogger


def configure(settings, debug=False):
    """Configure a :term:`metlog` client and sender, either based on the
    passed in :py:attr:`settings` or as a debug sender.
    """
    global _metlogger
    if debug:
        _metlogger = MetlogClient(DebugCaptureSender(), logger=u'qdo-worker')
    elif _metlogger is None:
        # don't reconfigure an already configured logger
        _metlogger = client_from_dict_config(settings)
