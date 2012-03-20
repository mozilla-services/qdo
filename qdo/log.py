# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from metlog.config import client_from_dict_config
from metlog.client import MetlogClient
from metlog import senders

_metlogger = None


def get_logger():
    global _metlogger
    return _metlogger


def setup_debug_logging():
    global _metlogger
    metsender = senders.DebugCaptureSender()
    _metlogger = MetlogClient(metsender, logger=u'qdo-worker')


def configure_metlog(settings):
    global _metlogger
    if _metlogger is None:
        _metlogger = client_from_dict_config(settings)
