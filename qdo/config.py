# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozsvc.config import SettingsDict

ZOO_DEFAULT_NS = u'mozilla-qdo'
ZOO_DEFAULT_ROOT = u'/mozilla-qdo'


class QdoSettings(SettingsDict):
    """Settings representation including default values"""

    def __init__(self):
        super(QdoSettings, self).__init__()
        self.load_defaults()

    def load_defaults(self):
        """Populate settings with default values"""
        self[u'qdo-worker.wait_interval'] = 5
        self[u'qdo-worker.ca_bundle'] = None
        self[u'qdo-worker.context'] = u'qdo.worker:dict_context'
        self[u'qdo-worker.job'] = None

        self[u'queuey.connection'] = u'https://127.0.0.1:5001/v1/queuey/'
        self[u'queuey.app_key'] = None

        self[u'zookeeper.connection'] = \
            u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187'
        self[u'zookeeper.namespace'] = ZOO_DEFAULT_NS

        self[u'metlog.logger'] = u'qdo-worker'
        self[u'metlog.sender'] = {}
        self[u'metlog.sender'][u'class'] = u'metlog.senders.StdOutSender'
