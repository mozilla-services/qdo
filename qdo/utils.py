# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

from metlog.client import MetlogClient
from metlog import senders


# TODO: configure real sender
if 'nosetests' in sys.argv[0]:
    metsender = senders.DebugCaptureSender()
else: # pragma: no cover
    metsender = senders.StdOutSender()

metlogger = MetlogClient(metsender, logger='qdo-worker')
