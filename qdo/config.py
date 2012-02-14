# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

from mozsvc.config import SettingsDict

ZOO_DEFAULT_NS = 'mozilla-qdo'


class QdoSettings(SettingsDict):

    def __init__(self):
        super(QdoSettings, self).__init__()
        self.load_defaults()

    def load_defaults(self):
        self['qdo-worker.wait_interval'] = 5
        self['qdo-worker.zookeeper_connection'] = '127.0.0.1:2181'
        self['qdo-worker.zookeeper_namespace'] = ZOO_DEFAULT_NS
