# -*- coding: utf-8 -*-
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

ZOO_DEFAULT_NS = u'mozilla-qdo'
ZOO_DEFAULT_ROOT = u'/' + ZOO_DEFAULT_NS
ZOO_DEFAULT_HOST = u'127.0.0.1:2181,127.0.0.1:2184,127.0.0.1:2187'
ZOO_DEFAULT_CONN = ZOO_DEFAULT_HOST + ZOO_DEFAULT_ROOT


class SettingsDict(dict):
    """A dict subclass with some extra helpers for dealing with app settings.

    This class extends the standard dictionary interface with some extra helper
    methods that are handy when dealing with application settings. It expects
    the keys to be dotted setting names, where each component indicates one
    section in the settings hierarchy. You get the following extras:

        * setdefaults:  copy any unset settings from another dict
        * getsection:   return a dict of settings for just one subsection
    """

    separator = "."

    def copy(self):
        """D.copy() -> a shallow copy of D.

        This overrides the default dict.copy method to ensure that the
        copy is also an instance of SettingsDict.
        """
        new_items = self.__class__()
        for k, v in self.iteritems():
            new_items[k] = v
        return new_items

    def getsection(self, section):
        """Get a dict for just one sub-section of the config.

        This method extracts all the keys belonging to the name section and
        returns those values in a dict. The section name is removed from
        each key. For example::

            >>> c = SettingsDict({"a.one": 1, "a.two": 2, "b.three": 3})
            >>> c.getsection("a")
            {"one": 1, "two", 2}
            >>>
            >>> c.getsection("b")
            {"three": 3}
            >>>
            >>> c.getsection("c")
            {}

        """
        section_items = self.__class__()
        # If the section is "" then get keys without a section.
        if not section:
            for key, value in self.iteritems():
                if self.separator not in key:
                    section_items[key] = value
        # Otherwise, get keys prefixed with that section name.
        else:
            prefix = section + self.separator
            for key, value in self.iteritems():
                if key.startswith(prefix):
                    section_items[key[len(prefix):]] = value
        return section_items

    def setdefaults(self, *args, **kwds):
        """Import unset keys from another dict.

        This method lets you update the dict using defaults from another
        dict and/or using keyword arguments. It's like the standard update()
        method except that it doesn't overwrite existing keys.
        """
        for arg in args:
            if hasattr(arg, "keys"):
                for k in arg:
                    self.setdefault(k, arg[k])
            else:
                for k, v in arg:
                    self.setdefault(k, v)
        for k, v in kwds.iteritems():
            self.setdefault(k, v)


class QdoSettings(SettingsDict):
    """Settings representation including default values"""

    def __init__(self):
        super(QdoSettings, self).__init__()
        self.load_defaults()

    def load_defaults(self):
        """Populate settings with default values"""
        self[u'qdo-worker.wait_interval'] = 5
        self[u'qdo-worker.ca_bundle'] = None
        self[u'qdo-worker.job'] = None
        self[u'qdo-worker.job_context'] = u'qdo.worker:dict_context'

        self[u'queuey.connection'] = u'https://127.0.0.1:5001/v1/queuey/'
        self[u'queuey.app_key'] = None

        self[u'zookeeper.connection'] = ZOO_DEFAULT_CONN

        self[u'metlog.logger'] = u'qdo-worker'
        self[u'metlog.sender'] = {}
        self[u'metlog.sender'][u'class'] = u'metlog.senders.StdOutSender'
