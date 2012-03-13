# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozsvc.config import SettingsDict

ZOO_DEFAULT_NS = 'mozilla-qdo'


class QdoSettings(SettingsDict):
    """Settings representation including default values"""

    def __init__(self):
        super(QdoSettings, self).__init__()
        self.load_defaults()

    def load_defaults(self):
        """Populate settings with default values"""
        self['qdo-worker.wait_interval'] = 5
        self['qdo-worker.ca_bundle'] = None

        self['queuey.connection'] = 'https://127.0.0.1:5001/v1/queuey/'
        self['queuey.app_key'] = None

        self['zookeeper.connection'] = \
            '127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187'
        self['zookeeper.namespace'] = ZOO_DEFAULT_NS

        self['metlog.logger'] = 'qdo-worker'
        self['metlog.sender'] = {}
        self['metlog.sender']['class'] = 'metlog.senders.StdOutSender'
